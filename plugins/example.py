from telethon import events

class TelethonPlugin:
    def __init__(self, bot):
        self.bot = bot

    def register_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/hello'))
        async def hello(event):
            await event.reply("Hello! This is the example plugin 👋")

        @self.bot.on(events.NewMessage(pattern='/echo (.+)'))
        async def echo(event):
            text = event.pattern_match.group(1)
            await event.reply(f"Echo: {text}")
