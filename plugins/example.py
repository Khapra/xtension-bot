"""Example plugin demonstrating the plugin structure - v1.1.0"""

from telethon import events

class TelethonPlugin:
    """
    Example plugin showing the standard plugin structure.
    Every plugin must have:
    1. A class named TelethonPlugin
    2. An __init__ method that accepts the bot instance
    3. A commands dictionary listing all commands
    4. A register_handlers method to register event handlers
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.commands = {
            "/hello": "Simple greeting message",
            "/echo <text>": "Echo back your message",
            "/bold <text>": "Make text bold",
            "/italic <text>": "Make text italic"
        }
    
    def register_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/hello'))
        async def hello(event):
            """Simple greeting handler"""
            sender = await event.get_sender()
            await event.reply(f'Hello {sender.first_name}! This is the example plugin 👋')
        
        @self.bot.on(events.NewMessage(pattern='/echo (.+)'))
        async def echo(event):
            """Echo back the user's message"""
            text = event.pattern_match.group(1)
            await event.reply(f"Echo: {text}")
        
        @self.bot.on(events.NewMessage(pattern='/bold (.+)'))
        async def bold(event):
            """Make text bold"""
            text = event.pattern_match.group(1)
            await event.reply(f"**{text}**", parse_mode='md')
        
        @self.bot.on(events.NewMessage(pattern='/italic (.+)'))
        async def italic(event):
            """Make text italic"""
            text = event.pattern_match.group(1)
            await event.reply(f"_{text}_", parse_mode='md')
