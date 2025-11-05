"""Information and system status plugin with rate limiting"""

from telethon import events
import platform
import os
import sys
from datetime import datetime

class TelethonPlugin:
    def __init__(self, bot):
        self.bot = bot
        self.commands = {
            "/info": "Get general bot information",
            "/sysinfo": "Get detailed system information",
            "/botinfo": "Get bot-specific information"
        }
    
    def register_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/info'))
        async def info_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            self.bot.commands_processed += 1
            
            # Calculate uptime
            uptime = datetime.now() - self.bot._start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours}h {minutes}m {seconds}s"
            
            info_text = f"""ℹ️ **Bot Information**
            
**Name:** @{self.bot.me.username}
**Version:** {self.bot.version}
**Uptime:** {uptime_str}
**Plugins Loaded:** {len(self.bot.plugins)}
**Commands Processed:** {self.bot.commands_processed}

**Platform:** {platform.system()} {platform.release()}
**Python:** {sys.version.split()[0]}

_Use /sysinfo for detailed system information_
"""
            await event.reply(info_text, parse_mode='md')
        
        @self.bot.on(events.NewMessage(pattern='/sysinfo'))
        async def sysinfo_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            self.bot.commands_processed += 1
            
            # Get system information
            try:
                import psutil
                
                # CPU info
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_cores = psutil.cpu_count()
                
                # Memory info
                memory = psutil.virtual_memory()
                memory_used = memory.used / (1024**3)  # GB
                memory_total = memory.total / (1024**3)  # GB
                memory_percent = memory.percent
                
                # Disk info
                disk = psutil.disk_usage('/')
                disk_used = disk.used / (1024**3)  # GB
                disk_total = disk.total / (1024**3)  # GB
                disk_percent = disk.percent
                
                # Process info
                process = psutil.Process(os.getpid())
                process_memory = process.memory_info().rss / (1024**2)  # MB
                process_threads = process.num_threads()
                
                sys_text = f"""🖥️ **System Information**
                
**📊 CPU:**
• Usage: {cpu_percent}%
• Cores: {cpu_cores}

**💾 Memory:**
• Used: {memory_used:.1f} GB / {memory_total:.1f} GB
• Usage: {memory_percent}%

**💿 Disk:**
• Used: {disk_used:.1f} GB / {disk_total:.1f} GB
• Usage: {disk_percent}%

**🤖 Bot Process:**
• Memory: {process_memory:.1f} MB
• Threads: {process_threads}

**🖥️ System:**
• OS: {platform.system()} {platform.release()}
• Architecture: {platform.machine()}
• Python: {sys.version.split()[0]}
"""
            except ImportError:
                sys_text = f"""🖥️ **System Information**
                
**Platform:** {platform.system()} {platform.release()}
**Architecture:** {platform.machine()}
**Python:** {sys.version.split()[0]}
**Processor:** {platform.processor() or 'Unknown'}

_Note: Install psutil for detailed system stats_
"""
            
            await event.reply(sys_text, parse_mode='md')
        
        @self.bot.on(events.NewMessage(pattern='/botinfo'))
        async def botinfo_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            self.bot.commands_processed += 1
            
            # Count total commands
            total_commands = 0
            for plugin in self.bot.plugins.values():
                if hasattr(plugin, 'commands'):
                    total_commands += len(plugin.commands)
            
            # Core commands
            total_commands += 10  # Core + admin commands (including new /ratelimit)
            
            # Get admin info
            admin_count = len(self.bot.admin_ids) if self.bot.admin_ids else 0
            admin_mode = "Restricted" if admin_count > 0 else "All users are admins"
            
            # Get rate limit info
            rl_info = f"{self.bot.rate_limiter.commands_per_minute}/min, {self.bot.rate_limiter.commands_per_hour}/hour"
            
            bot_text = f"""🤖 **Bot Details**
            
**Bot Username:** @{self.bot.me.username}
**Bot ID:** {self.bot.me.id}
**Bot Name:** {self.bot.me.first_name}
**Version:** {self.bot.version}

**📊 Statistics:**
• Total Commands: {total_commands}
• Commands Processed: {self.bot.commands_processed}
• Plugins Loaded: {len(self.bot.plugins)}

**🔐 Security:**
• Admin Mode: {admin_mode}
• Admin Users: {admin_count}
• Rate Limiting: {rl_info}

**⚙️ Configuration:**
• Session Type: {self.bot.config.session_type}
• Log Level: {os.getenv('LOG_LEVEL', 'INFO')}
• Plugin System: {'Enabled' if self.bot.config.enable_plugins else 'Disabled'}

**📦 Repository:**
[github.com/Khapra/xtension-bot](https://github.com/Khapra/xtension-bot)
"""
            await event.reply(bot_text, parse_mode='md')
