"""Example plugin demonstrating the plugin structure with rate limiting"""

from telethon import events

class TelethonPlugin:
    def __init__(self, bot):
        self.bot = bot
        self.commands = {
            "/hello": "Simple greeting command",
            "/echo <text>": "Echo back your message",
            "/bold <text>": "Make text bold",
            "/italic <text>": "Make text italic"
        }
    
    def register_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/hello'))
        async def hello_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            self.bot.commands_processed += 1
            sender = await event.get_sender()
            await event.reply(f'Hello {sender.first_name}! 👋\n\nThis is an example plugin command.')
        
        @self.bot.on(events.NewMessage(pattern='/echo (.+)'))
        async def echo_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            self.bot.commands_processed += 1
            text = event.pattern_match.group(1)
            await event.reply(f"🔊 Echo: {text}")
        
        @self.bot.on(events.NewMessage(pattern='/bold (.+)'))
        async def bold_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            self.bot.commands_processed += 1
            text = event.pattern_match.group(1)
            await event.reply(f"**{text}**", parse_mode='md')
        
        @self.bot.on(events.NewMessage(pattern='/italic (.+)'))
        async def italic_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            self.bot.commands_processed += 1
            text = event.pattern_match.group(1)
            await event.reply(f"_{text}_", parse_mode='md')
