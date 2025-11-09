"""Core bot implementation using Telethon

Xtension Bot v1.3.8
2025-11-09

Features:
- Plugin system, admin system, rate limiting, hot-reload, logging.
- Correct API warning logic for demo/fallback keys.
- Safe sender name display in core handlers.
"""

import logging
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict
from functools import wraps

from telethon import TelegramClient, events, Button
from telethon.sessions import SQLiteSession, MemorySession

from .config import Config
from .rate_limiter import RateLimiter

# === Logging setup ===
logger = logging.getLogger(__name__)

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
if log_level == "DEBUG":
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)-8s | %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Reduce Telethon's internal logging noise
    logging.getLogger('telethon.network.mtprotosender').setLevel(logging.INFO)
    logging.getLogger('telethon.extensions.messagepacker').setLevel(logging.INFO)
    logger.debug("Debug mode enabled - verbose logging active")
else:
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='[%(asctime)s] %(levelname)-8s | %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def debug_log_command(handler_name):
    """Decorator to log command execution in debug mode"""
    def decorator(func):
        @wraps(func)
        async def wrapper(event):
            if logger.isEnabledFor(logging.DEBUG):
                sender = await event.get_sender()
                sender_info = None
                # Defensive display for debug
                if hasattr(sender, "first_name") and sender.first_name:
                    sender_info = sender.first_name
                elif hasattr(sender, "title") and sender.title:
                    sender_info = sender.title
                elif hasattr(sender, "username") and sender.username:
                    sender_info = f"@{sender.username}"
                else:
                    sender_info = "Unknown"
                if hasattr(event, 'pattern_match') and event.pattern_match:
                    command = event.pattern_match.string
                    logger.debug(f"[COMMAND] {handler_name}: '{command}' from {sender_info}")
                elif hasattr(event, 'data'):
                    logger.debug(f"[BUTTON] {handler_name}: {event.data.decode()} from {sender_info}")
                else:
                    logger.debug(f"[EVENT] {handler_name} triggered by {sender_info}")
            try:
                result = await func(event)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"[SUCCESS] {handler_name} completed")
                return result
            except Exception as e:
                logger.error(f"[ERROR] {handler_name} failed: {e}")
                if logger.isEnabledFor(logging.DEBUG):
                    import traceback
                    logger.debug(traceback.format_exc())
                raise
        return wrapper
    return decorator

def _read_version_from_file() -> str:
    candidates = []
    try:
        repo_root = Path(__file__).resolve().parents[1]
        candidates.append(repo_root / "VERSION")
        candidates.append(Path("/app/VERSION"))
        for p in candidates:
            if p.exists():
                return p.read_text("utf-8").strip()
    except Exception:
        pass
    return "unknown"

def safe_sender_display(sender):
    """Safely display sender's identity: works for user, bot, group, channel"""
    if hasattr(sender, "first_name") and sender.first_name:
        return sender.first_name
    if hasattr(sender, "title") and sender.title:
        return sender.title
    if hasattr(sender, "username") and sender.username:
        return f"@{sender.username}"
    return "Unknown"

class XtensionBot(TelegramClient):
    """Main bot class with plugin system and admin commands"""

    def __init__(self, config: Config):
        self.config = config
        api_id, api_hash = config.get_api_credentials()

        logger.debug(f"Initializing bot with session type: {config.session_type}")

        if config.session_type == "memory":
            session = MemorySession()
        else:
            session_path = Path(config.session_dir) / f"{config.session_name}.session"
            session_path.parent.mkdir(exist_ok=True)
            session = SQLiteSession(str(session_path))
            logger.debug(f"Session path: {session_path}")

        # Call parent TelethonClient init with actual credentials
        super().__init__(
            session, api_id, api_hash,
            connection_retries=5, 
            request_retries=5
        )

        self.plugins: Dict[str, object] = {}
        self._start_time = datetime.now()
        self.version = _read_version_from_file()
        self.commands_processed = 0

        # Admin configuration
        self.admin_ids = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
        logger.debug(f"Admin IDs configured: {self.admin_ids if self.admin_ids else 'None (all users are admins)'}")

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            commands_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "30")),
            commands_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "300")),
            burst_limit=int(os.getenv("RATE_LIMIT_BURST", "5")),
            burst_window=int(os.getenv("RATE_LIMIT_BURST_WINDOW", "10")),
            cooldown_time=int(os.getenv("RATE_LIMIT_COOLDOWN", "60"))
        )
        logger.debug(f"Rate limiter initialized: {self.rate_limiter.commands_per_minute}/min, {self.rate_limiter.commands_per_hour}/hour")

    async def start(self):
        """Start the bot and initialize all systems"""
        logger.info(f"Starting Xtension Bot v{self.version}...")
        logger.debug("Connecting to Telegram servers...")

        api_id, api_hash = self.config.get_api_credentials()

        await super().start(bot_token=self.config.bot_token)
        self.me = await self.get_me()

        # Warn if using demo or public fallback keys (check ACTUAL values used)
        if (
            (api_id == 149344 and api_hash == "1c760da900d9a3e28b17c16410680dae") or
            (api_id == 6 and api_hash == "eb06d4abfb49dc3eeb1aeb98ae0f581e")
        ):
            print(
                "\n"
                "⚠️  WARNING: Bot is running with DEMO or DEFAULT TELEGRAM API ID/HASH!\n"
                f"(Current: {api_id}, {api_hash})\n"
                "This is for TESTING only. For production, obtain your own API keys at https://my.telegram.org and set them in your .env file!\n"
            )
            
        logger.info(f"Logged in as @{self.me.username} (ID: {self.me.id})")
        logger.debug(f"Bot name: {self.me.first_name}")

        logger.debug("Registering core handlers...")
        self._register_handlers()
        handler_count = len(self.list_event_handlers())
        logger.debug(f"Registered {handler_count} core handlers")

        if self.config.enable_plugins:
            logger.debug(f"Loading plugins from {self.config.plugin_dir}")
            await self._load_plugins()
        else:
            logger.info("Plugin system disabled")

        print(f"\n{'='*50}")
        print(f"✅ XTENSION BOT v{self.version} READY!")
        print(f"🤖 Bot: @{self.me.username}")
        print(f"🔌 Plugins: {len(self.plugins)} loaded")
        print(f"📝 Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")
        print(f"🛡️ Rate Limiting: {self.rate_limiter.commands_per_minute}/min")
        print(f"{'='*50}\n")

        logger.info(f"Bot ready with {len(self.plugins)} plugins loaded")

        await self.run_until_disconnected()

    def is_admin(self, user_id):
        """Check if user has admin privileges"""
        is_admin = not self.admin_ids or user_id in self.admin_ids
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Admin check for user {user_id}: {'✓' if is_admin else '✗'}")
        return is_admin

    async def check_rate_limit(self, event):
        """Check if user is rate limited"""
        if self.is_admin(event.sender_id):
            return False  # Admins bypass rate limits
        
        is_limited, message = self.rate_limiter.is_rate_limited(event.sender_id)
        if is_limited:
            await event.reply(message)
            return True
        return False

    def _register_handlers(self):
        """Register all core command handlers"""

        @self.on(events.NewMessage(pattern='/start'))
        @debug_log_command("start")
        async def start_handler(event):
            if await self.check_rate_limit(event):
                return
            self.commands_processed += 1
            sender = await event.get_sender()
            admin_text = " (Admin)" if self.is_admin(event.sender_id) else ""
            who = safe_sender_display(sender)
            await event.reply(
                f"👋 Welcome {who}{admin_text}!\n\n"
                f"🤖 **Xtension Bot v{self.version}**\n"
                f"A powerful, extensible Telegram bot framework\n\n"
                f"Use /help to see all commands.",
                buttons=[[Button.inline("📚 Help", b"show_help")]]
            )

        @self.on(events.CallbackQuery(data=b"show_help"))
        @debug_log_command("help_button")
        async def help_button(event):
            if await self.check_rate_limit(event):
                return
            self.commands_processed += 1
            commands = self._get_all_commands(event.sender_id)
            text = self._format_help_text(commands)
            await event.answer("Help menu opened!")
            await event.edit(text, parse_mode='md')

        @self.on(events.NewMessage(pattern='/help'))
        @debug_log_command("help")
        async def help_handler(event):
            if await self.check_rate_limit(event):
                return
            self.commands_processed += 1
            commands = self._get_all_commands(event.sender_id)
            text = self._format_help_text(commands)
            await event.reply(text, parse_mode='md')

        @self.on(events.NewMessage(pattern='/ping'))
        @debug_log_command("ping")
        async def ping_handler(event):
            if await self.check_rate_limit(event):
                return
            self.commands_processed += 1
            await event.reply("🏓 Pong!")

        @self.on(events.NewMessage(pattern='/plugins'))
        @debug_log_command("plugins")
        async def plugins_handler(event):
            if await self.check_rate_limit(event):
                return
            self.commands_processed += 1
            if self.plugins:
                plugin_info = []
                for name, plugin in sorted(self.plugins.items()):
                    cmd_count = len(getattr(plugin, 'commands', {}))
                    plugin_info.append(f"• **{name}** ({cmd_count} commands)")
                text = "🔌 **Loaded Plugins:**\n\n" + "\n".join(plugin_info)
                text += f"\n\n_Total: {len(self.plugins)} plugins_"
            else:
                text = "No plugins loaded"
            await event.reply(text, parse_mode='md')
        
        @self.on(events.NewMessage(pattern='/version'))
        @debug_log_command("version")
        async def version_handler(event):
            if await self.check_rate_limit(event):
                return
            self.commands_processed += 1
            uptime = datetime.now() - self._start_time
            await event.reply(
                f"🤖 **Xtension Bot**\n"
                f"Version: {self.version}\n"
                f"Uptime: {str(uptime).split('.')[0]}\n"
                f"Commands: {self.commands_processed} processed\n\n"
                f"[GitHub Repository](https://github.com/Khapra/xtension-bot)",
                parse_mode='md'
            )

        # === ADMIN COMMANDS ===

        @self.on(events.NewMessage(pattern='/reload'))
        @debug_log_command("reload")
        async def reload_handler(event):
            self.commands_processed += 1
            if not self.is_admin(event.sender_id):
                logger.warning(f"Unauthorized reload attempt by user {event.sender_id}")
                await event.reply("❌ This command is for admins only!")
                return
            
            logger.info("Reloading plugins...")
            msg = await event.reply("🔄 Reloading plugins...")
            
            old_plugins = list(self.plugins.keys())
            self.plugins.clear()
            
            # Clear sys.modules for plugins
            modules_to_remove = [m for m in sys.modules.keys() if m.startswith('plugins.')]
            for module in modules_to_remove:
                logger.debug(f"Removing module: {module}")
                del sys.modules[module]
            
            # Reload plugins
            await self._load_plugins()
            
            new_plugins = list(self.plugins.keys())
            added = set(new_plugins) - set(old_plugins)
            removed = set(old_plugins) - set(new_plugins)
            
            logger.info(f"Reload complete: {len(new_plugins)} plugins loaded")
            if added:
                logger.info(f"Added plugins: {', '.join(added)}")
            if removed:
                logger.info(f"Removed plugins: {', '.join(removed)}")
            
            response = "✅ **Reload Complete**\n\n"
            if new_plugins:
                response += f"📦 **Loaded Plugins:**\n"
                for name, plugin in sorted(self.plugins.items()):
                    cmd_count = len(getattr(plugin, 'commands', {}))
                    response += f"  • {name}: {cmd_count} commands\n"
            else:
                response += "• No plugins loaded\n"
            
            if added:
                response += f"\n➕ **Added:** {', '.join(sorted(added))}\n"
            if removed:
                response += f"\n➖ **Removed:** {', '.join(sorted(removed))}\n"
            
            await msg.edit(response, parse_mode='md')
        
        @self.on(events.NewMessage(pattern='/restart'))
        @debug_log_command("restart")
        async def restart_handler(event):
            self.commands_processed += 1
            if not self.is_admin(event.sender_id):
                logger.warning(f"Unauthorized restart attempt by user {event.sender_id}")
                await event.reply("❌ This command is for admins only!")
                return
            
            logger.info("Bot restart requested")
            await event.reply("🔄 Restarting bot process...")
            await asyncio.sleep(2)
            
            logger.info("Restarting process...")
            os.execv(sys.executable, ['python', '-m', 'bot'])
        
        @self.on(events.NewMessage(pattern='/shutdown'))
        @debug_log_command("shutdown")
        async def shutdown_handler(event):
            self.commands_processed += 1
            if not self.is_admin(event.sender_id):
                logger.warning(f"Unauthorized shutdown attempt by user {event.sender_id}")
                await event.reply("❌ This command is for admins only!")
                return
            
            logger.info("Bot shutdown requested")
            await event.reply("👋 Shutting down bot...")
            await self.disconnect()
            sys.exit(0)
        
        @self.on(events.NewMessage(pattern='/stats'))
        @debug_log_command("stats")
        async def stats_handler(event):
            self.commands_processed += 1
            if not self.is_admin(event.sender_id):
                await event.reply("❌ This command is for admins only!")
                return
            
            uptime = datetime.now() - self._start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours}h {minutes}m {seconds}s"
            
            # Count total commands
            total_commands = 6  # Core commands
            if self.is_admin(event.sender_id):
                total_commands += 5  # Admin commands including /ratelimit
            
            for plugin in self.plugins.values():
                if hasattr(plugin, 'commands'):
                    total_commands += len(plugin.commands)
            
            # Get memory usage
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_str = f"{memory_mb:.1f} MB"
            except:
                memory_str = "N/A"
            
            # Get rate limit stats
            rl_stats = self.rate_limiter.get_global_stats()
            
            stats_text = f"""📊 **Bot Statistics**
            
🤖 **Bot:** @{self.me.username}
📌 **Version:** {self.version}
⏱ **Uptime:** {uptime_str}
📈 **Commands Processed:** {self.commands_processed}

🔌 **Plugins:** {len(self.plugins)} loaded
📝 **Total Commands:** {total_commands} available

🛡️ **Rate Limiting:**
• Commands Allowed: {rl_stats['total_commands_allowed']}
• Commands Blocked: {rl_stats['total_commands_limited']}
• Block Rate: {rl_stats['limit_percentage']}%
• Users Tracked: {rl_stats['total_users_tracked']}
• Users in Cooldown: {rl_stats['users_in_cooldown']}

🛠 **System:**
• Python: {sys.version.split()[0]}
• Platform: {sys.platform}
• Memory Usage: {memory_str}
• Session: {self.config.session_type}
• Log Level: {os.getenv('LOG_LEVEL', 'INFO')}
"""
            await event.reply(stats_text, parse_mode='md')
        
        @self.on(events.NewMessage(pattern='/ratelimit'))
        @debug_log_command("ratelimit")
        async def ratelimit_handler(event):
            self.commands_processed += 1
            if not self.is_admin(event.sender_id):
                await event.reply("❌ This command is for admins only!")
                return
            
            # Parse command: /ratelimit [stats|reset <user_id>|global]
            parts = event.text.split()
            
            if len(parts) == 1 or parts[1] == "global":
                # Show global stats
                stats = self.rate_limiter.get_global_stats()
                text = f"""📊 **Rate Limiting Statistics**
                
**Active Users:** {stats['total_users_tracked']}
**Users Limited:** {stats['users_in_cooldown']}
**Commands Allowed:** {stats['total_commands_allowed']}
**Commands Blocked:** {stats['total_commands_limited']}
**Block Rate:** {stats['limit_percentage']}%

**Current Limits:**
• Per Minute: {self.rate_limiter.commands_per_minute}
• Per Hour: {self.rate_limiter.commands_per_hour}
• Burst: {self.rate_limiter.burst_limit} in {self.rate_limiter.burst_window}s
"""
                await event.reply(text, parse_mode='md')
            
            elif parts[1] == "reset" and len(parts) > 2:
                # Reset specific user
                try:
                    target_user = int(parts[2])
                    self.rate_limiter.reset_user(target_user)
                    await event.reply(f"✅ Reset rate limits for user {target_user}")
                except ValueError:
                    await event.reply("❌ Invalid user ID")
            
            elif parts[1] == "stats" and len(parts) > 2:
                # Show user stats
                try:
                    target_user = int(parts[2])
                    stats = self.rate_limiter.get_user_stats(target_user)
                    text = f"""👤 **User {target_user} Rate Limit Stats**
                    
**Last Minute:** {stats['commands_last_minute']}/{stats['limit_per_minute']}
**Last Hour:** {stats['commands_last_hour']}/{stats['limit_per_hour']}
**Cooldown:** {'Yes' if stats['in_cooldown'] else 'No'}
"""
                    if stats['in_cooldown']:
                        text += f"**Cooldown Remaining:** {stats['cooldown_remaining']}s"
                    await event.reply(text, parse_mode='md')
                except ValueError:
                    await event.reply("❌ Invalid user ID")
            
            else:
                await event.reply("Usage: /ratelimit [global|stats <user_id>|reset <user_id>]")

    def _get_all_commands(self, user_id):
        """Dynamically get all available commands based on loaded plugins"""
        logger.debug(f"Getting commands for user {user_id}")

        commands = {
            "📍 Core Commands": {
                "/start": "Show welcome message and bot information",
                "/help": "Display all available commands",
                "/ping": "Check if bot is responsive",
                "/plugins": "List all loaded plugins",
                "/version": "Show bot version and info"
            }
        }

        # Add admin commands if user is admin
        if self.is_admin(user_id):
            commands["🔐 Admin Commands"] = {
                "/reload": "Hot-reload all plugins without restart",
                "/restart": "Restart the bot process completely",
                "/shutdown": "Stop the bot",
                "/stats": "Detailed bot statistics",
                "/ratelimit": "Manage rate limiting (view stats, reset users)"
            }

        # Dynamically add plugin commands from loaded plugins
        for plugin_name, plugin in sorted(self.plugins.items()):
            if hasattr(plugin, 'commands') and plugin.commands:
                category = f"🔌 {plugin_name.capitalize()} Plugin"
                commands[category] = plugin.commands
                logger.debug(f"Added {len(plugin.commands)} commands from {plugin_name}")

        return commands

    def _format_help_text(self, commands):
        """Format commands dictionary into readable help text"""
        text = f"📚 **Xtension Bot v{self.version} Commands**\n\n"

        total_commands = 0
        for category, cmds in commands.items():
            text += f"**{category}:**\n"
            if isinstance(cmds, dict):
                for cmd, desc in cmds.items():
                    text += f"• `{cmd}` — {desc}\n"
                    total_commands += 1
            else:
                # Fallback for old format (shouldn't happen)
                for cmd in cmds:
                    text += f"• {cmd}\n"
                    total_commands += 1
            text += "\n"

        text += f"_Total: {total_commands} commands available_"
        return text

    async def _load_plugins(self):
        """Load all plugins from the plugins directory with automatic logging and rate limiting"""
        plugin_dir = Path(self.config.plugin_dir)
        plugin_dir.mkdir(exist_ok=True)

        logger.debug(f"Plugin directory: {plugin_dir.absolute()}")

        # Create example plugin if directory is empty
        example = plugin_dir / "example.py"
        if not any(plugin_dir.glob("*.py")):
            logger.info("No plugins found, creating example plugin")
            example.write_text('''"""Example plugin demonstrating the plugin structure"""

from telethon import events

class TelethonPlugin:
    def __init__(self, bot):
        self.bot = bot
        self.commands = {
            "/hello": "Greeting from example plugin",
            "/echo <text>": "Echo back your message"
        }
    
    def register_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/hello'))
        async def hello(event):
            if await self.bot.check_rate_limit(event):
                return
            sender = await event.get_sender()
            await event.reply(f'Hello {sender.first_name}! This is the example plugin 👋')
        
        @self.bot.on(events.NewMessage(pattern='/echo (.+)'))
        async def echo(event):
            if await self.bot.check_rate_limit(event):
                return
            text = event.pattern_match.group(1)
            await event.reply(f"Echo: {text}")
''')

        loaded_count = 0
        failed_plugins = []

        # Load each Python file as a plugin
        for plugin_file in sorted(plugin_dir.glob("*.py")):
            if plugin_file.name.startswith("_"):
                logger.debug(f"Skipping {plugin_file.name} (starts with underscore)")
                continue

            logger.debug(f"Loading plugin: {plugin_file.name}")
            try:
                # Import the plugin module
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{plugin_file.stem}", 
                    plugin_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check for TelethonPlugin class
                if hasattr(module, "TelethonPlugin"):
                    plugin = module.TelethonPlugin(self)
                    
                    # Register handlers with logging wrapper in debug mode
                    if hasattr(plugin, "register_handlers"):
                        if logger.isEnabledFor(logging.DEBUG):
                            from .plugin_wrapper import create_logged_handler
                            original_on = self.on

                            def logged_on(event_type):
                                def decorator(handler):
                                    wrapped = create_logged_handler(handler, plugin_file.stem, self)
                                    return original_on(event_type)(wrapped)
                                return decorator

                            self.on = logged_on
                            plugin.register_handlers()
                            self.on = original_on
                            logger.debug(f"Registered handlers for {plugin_file.stem} with logging")
                        else:
                            plugin.register_handlers()
                            logger.debug(f"Registered handlers for {plugin_file.stem}")

                    # Store plugin instance
                    self.plugins[plugin_file.stem] = plugin
                    loaded_count += 1

                    # Log plugin info
                    cmd_count = len(getattr(plugin, 'commands', {}))
                    logger.info(f"Loaded plugin: {plugin_file.stem} ({cmd_count} commands)")
                else:
                    logger.warning(f"Plugin {plugin_file.name} has no TelethonPlugin class")
                    failed_plugins.append(plugin_file.stem)
                    
            except Exception as e:
                logger.error(f"Failed loading plugin {plugin_file.name}: {e}")
                if logger.isEnabledFor(logging.DEBUG):
                    import traceback
                    logger.debug(traceback.format_exc())
                failed_plugins.append(plugin_file.stem)

        # Summary
        if failed_plugins:
            logger.warning(f"Failed to load plugins: {', '.join(failed_plugins)}")

        logger.info(f"Plugin loading complete: {loaded_count} loaded, {len(failed_plugins)} failed")
        