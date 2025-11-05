"""Fun and entertainment plugin - v1.1.0"""

from telethon import events
import random
from datetime import datetime

class TelethonPlugin:
    def __init__(self, bot):
        self.bot = bot
        self.commands = {
            "/joke": "Get a random programmer joke",
            "/dice": "Roll a dice (1-6)",
            "/coin": "Flip a coin",
            "/8ball <question>": "Ask the magic 8-ball",
            "/choose <opt1, opt2, ...>": "Choose randomly from options",
            "/rate <thing>": "Rate something randomly"
        }
        
    def register_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/joke'))
        async def joke(event):
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
                "How many programmers does it take to change a light bulb? None, it's a hardware problem. 💡",
                "Why do Python programmers wear glasses? Because they can't C. 👓",
                "Why did the developer go broke? Because he used up all his cache! 💰",
                "Git commit -m 'One does not simply merge into master' 😅",
                "Why do Java developers wear glasses? Because they don't C#! 👓",
                "A SQL query walks into a bar, sees two tables and asks: 'Can I join you?' 🍺",
                "How do you comfort a JavaScript bug? You console it! 🎮",
                "Why did the Python programmer not respond? Because they were in de-bug mode! 🐍",
                "404: Joke not found... Just kidding! 😄",
                "There are only 10 types of people: those who understand binary and those who don't. 🤓",
                "Why did the programmer quit? Because they didn't get arrays! 📊",
                "!false - It's funny because it's true! 😂",
                "Algorithm: A word used by programmers when they don't want to explain what they did. 🤷",
                "// This comment is self-documenting 📝"
            ]
            await event.reply(f"😄 {random.choice(jokes)}")
            
        @self.bot.on(events.NewMessage(pattern='/dice'))
        async def dice(event):
            result = random.randint(1, 6)
            dice_emoji = ["", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"][result]
            await event.reply(f"{dice_emoji} You rolled: **{result}**!", parse_mode='md')
            
        @self.bot.on(events.NewMessage(pattern='/coin'))
        async def coin(event):
            result = random.choice(["Heads 👑", "Tails 🪙"])
            await event.reply(f"🪙 Flipping... **{result}**!", parse_mode='md')
            
        @self.bot.on(events.NewMessage(pattern='/8ball (.+)'))
        async def eightball(event):
            responses = [
                "Yes, definitely! ✅",
                "No way! ❌", 
                "Ask again later 🔮",
                "Most likely 👍",
                "Don't count on it 👎",
                "Yes! 💯",
                "My sources say no 🚫",
                "Outlook good 📈",
                "Very doubtful 🤔",
                "Better not tell you now 🤐",
                "Cannot predict now 🌫️",
                "Concentrate and ask again 🧘",
                "Signs point to yes ✨",
                "My reply is no 🙅",
                "Without a doubt 💪",
                "As I see it, yes 👁️"
            ]
            question = event.pattern_match.group(1)
            answer = random.choice(responses)
            await event.reply(
                f"🎱 **Magic 8-Ball**\n\n"
                f"❓ Question: _{question}_\n"
                f"💭 Answer: **{answer}**",
                parse_mode='md'
            )
            
        @self.bot.on(events.NewMessage(pattern='/choose (.+)'))
        async def choose(event):
            text = event.pattern_match.group(1)
            # Split by comma, semicolon, or 'or'
            import re
            options = re.split('[,;]|\\s+or\\s+', text)
            options = [opt.strip() for opt in options if opt.strip()]
            
            if len(options) < 2:
                await event.reply(
                    "❌ Please provide at least 2 options\n"
                    "Example: `/choose pizza, burger, tacos`",
                    parse_mode='md'
                )
                return
            
            choice = random.choice(options)
            await event.reply(
                f"🤔 **Decision Time!**\n\n"
                f"Options: {', '.join(options)}\n"
                f"I choose: **{choice}**! 🎯",
                parse_mode='md'
            )
        
        @self.bot.on(events.NewMessage(pattern='/rate (.+)'))
        async def rate(event):
            thing = event.pattern_match.group(1)
            rating = random.randint(0, 10)
            
            # Fun responses based on rating
            if rating <= 3:
                comment = random.choice(["Meh 😑", "Not great 👎", "Could be better 🤷"])
            elif rating <= 6:
                comment = random.choice(["Decent 👍", "Not bad 😊", "Average 🤔"])
            elif rating <= 9:
                comment = random.choice(["Pretty good! 😄", "Nice! 👌", "Great! 🎉"])
            else:
                comment = "Perfect! 💯🔥"
            
            stars = "⭐" * rating + "☆" * (10 - rating)
            
            await event.reply(
                f"📊 **Rating: {thing}**\n\n"
                f"{stars}\n"
                f"Score: **{rating}/10**\n"
                f"{comment}",
                parse_mode='md'
            )
