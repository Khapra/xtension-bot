"""Core bot implementation using Telethon"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from telethon import TelegramClient, events, Button
from telethon.sessions import SQLiteSession, MemorySession

from .config import Config

logger = logging.getLogger(__name__)

class XtensionBot(TelegramClient):
    def __init__(self, config: Config):
        self.config = config
        api_id, api_hash = config.get_api_credentials()

        if config.session_type == "memory":
            session = MemorySession()
        else:
            session_path = Path(config.session_dir) / f"{config.session_name}.session"
            session_path.parent.mkdir(exist_ok=True)
            session = SQLiteSession(str(session_path))

        super().__init__(session, api_id, api_hash,
                         connection_retries=5, request_retries=5)

        self.plugins: Dict[str, object] = {}
        self._start_time = datetime.now()

    async def start(self):
        logger.info("Starting Xtension Bot...")
        await super().start(bot_token=self.config.bot_token)
        self.me = await self.get_me()
        logger.info(f"Logged in as @{self.me.username}")

        self._register_handlers()

        if self.config.enable_plugins:
            await self._load_plugins()

        print(f"✅ XTENSION BOT READY! @{self.me.username}")
        await self.run_until_disconnected()

    def _register_handlers(self):
        @self.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            sender = await event.get_sender()
            await event.reply(
                f"👋 Welcome {sender.first_name}! This is Xtension Bot.\nUse /help to see commands.",
                buttons=[[Button.inline("📚 Help", b"help")]]
            )

        @self.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            text = "📚 Xtension Bot Commands\n\n"
            text += "• /start — Welcome\n• /help — This message\n• /ping — Check bot\n• /plugins — List plugins\n"
            await event.reply(text)

        @self.on(events.NewMessage(pattern='/ping'))
        async def ping_handler(event):
            await event.reply("🏓 Pong!")

        @self.on(events.NewMessage(pattern='/plugins'))
        async def plugins_handler(event):
            if self.plugins:
                text = "🔌 Loaded plugins:\n" + "\n".join(f"• {n}" for n in self.plugins)
            else:
                text = "No plugins loaded"
            await event.reply(text)

    async def _load_plugins(self):
        plugin_dir = Path(self.config.plugin_dir)
        plugin_dir.mkdir(exist_ok=True)
        example = plugin_dir / "example.py"
        if not any(plugin_dir.glob("*.py")):
            example.write_text('''from telethon import events\n\nclass TelethonPlugin:\n    def __init__(self, bot):\n        self.bot = bot\n    def register_handlers(self):\n        @self.bot.on(events.NewMessage(pattern='/hello'))\n        async def hello(e):\n            await e.reply('Hello from example plugin!')\n''')

        for p in plugin_dir.glob("*.py"):
            if p.name.startswith("_"):
                continue
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"plugins.{p.stem}", p)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "TelethonPlugin"):
                    plugin = module.TelethonPlugin(self)
                    if hasattr(plugin, "register_handlers"):
                        plugin.register_handlers()
                    self.plugins[p.stem] = plugin
                    logger.info(f"Loaded plugin: {p.stem}")
            except Exception as e:
                logger.error(f"Failed loading plugin {p.name}: {e}")
