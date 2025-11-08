"""
Example Plugin for Xtension Bot (Telethon)

This template demonstrates:
- Defining commands with descriptions
- Handling messages, replies, admin checks, rate limits
- Safe sender info extraction (works for users, channels, groups)
- Sending media and formatted messages
- Error handling and logging
- Using environment config and plugin state
"""

import os
import random
import logging
from telethon import events

# --- Plugin configuration defaults ---
GREETING_EMOJI = os.getenv("EXAMPLE_GREETING_EMOJI", "👋")
JOKE_EMOJI = os.getenv("EXAMPLE_JOKE_EMOJI", "😂")
ADMIN_EMOJI = os.getenv("EXAMPLE_ADMIN_EMOJI", "🔐")

logger = logging.getLogger("example_plugin")
if not logger.hasHandlers():
    hdlr = logging.StreamHandler()
    hdlr.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s | %(message)s"))
    logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

class TelethonPlugin:
    def __init__(self, bot):
        self.bot = bot
        self.commands = {
            "/hello": "Greets the user with name or title",
            "/echo <text>": "Echoes back your message",
            "/bold <text>": "Replies with text in bold",
            "/joke": "Get a random programmer joke",
            "/adminhello": "Greets only admins",
            "/helpme": "Shows list of available example commands"
        }
        # Plugin state for demonstration (e.g., store last greeted user)
        self.last_greeted = None

    def register_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/hello'))
        async def hello_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            sender = await event.get_sender()
            who = self._safe_name(sender)
            self.last_greeted = who
            await event.reply(
                f"{GREETING_EMOJI} Hello, {who}! Welcome to Xtension Bot's example plugin."
            )

        @self.bot.on(events.NewMessage(pattern='/echo (.+)'))
        async def echo_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            text = event.pattern_match.group(1)
            await event.reply(f"🔊 Echo: {text}")

        @self.bot.on(events.NewMessage(pattern='/bold (.+)'))
        async def bold_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            text = event.pattern_match.group(1)
            await event.reply(f"**{text}**", parse_mode='md')

        @self.bot.on(events.NewMessage(pattern='/joke'))
        async def joke_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            joke = random.choice([
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "How many programmers does it take to change a light bulb? None, that's a hardware problem!",
                "Why do Java developers wear glasses? Because they don't C#!",
                "Why was the developer broke? Because they used up all their cache!",
                "There are only 10 types of people in the world: those who understand binary and those who don't."
            ])
            await event.reply(f"{JOKE_EMOJI} {joke}")

        @self.bot.on(events.NewMessage(pattern='/adminhello'))
        async def admin_hello_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            if not self.bot.is_admin(event.sender_id):
                await event.reply(f"{ADMIN_EMOJI} You are not an admin!")
                return
            sender = await event.get_sender()
            who = self._safe_name(sender)
            await event.reply(f"{ADMIN_EMOJI} Hello, admin {who}! 👑")

        @self.bot.on(events.NewMessage(pattern='/helpme'))
        async def helpme_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            # List all example plugin commands
            text = "**🤖 Example Plugin Help:**\n\n"
            for cmd, desc in self.commands.items():
                text += f"• `{cmd}` — {desc}\n"
            await event.reply(text, parse_mode='md')

        # Demonstrating replying to media message (file, sticker, etc)
        @self.bot.on(events.NewMessage(pattern='/mediaecho'))
        async def media_echo_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                if reply_msg.media:
                    await event.reply("🖼️ Echoing back your media:", file=reply_msg.media)
                else:
                    await event.reply("❌ Replied message has no media.")
            else:
                await event.reply("Reply to a message with media and use /mediaecho.")

    def _safe_name(self, sender):
        # Safely extract sender's display name (user, group, channel, bot...)
        if hasattr(sender, "first_name") and sender.first_name:
            return sender.first_name
        elif hasattr(sender, "title") and sender.title:
            return sender.title
        elif hasattr(sender, "username") and sender.username:
            return f"@{sender.username}"
        return "Unknown"

# End of example plugin file