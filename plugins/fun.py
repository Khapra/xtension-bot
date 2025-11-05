"""Fun commands plugin for entertainment with rate limiting"""

from telethon import events
import random

class TelethonPlugin:
    def __init__(self, bot):
        self.bot = bot
        self.commands = {
            "/joke": "Get a random programmer joke",
            "/dice": "Roll a dice (1-6)",
            "/coin": "Flip a coin",
            "/8ball <question>": "Ask the magic 8-ball",
            "/choose <option1,option2,...>": "Choose between multiple options",
            "/rate <thing>": "Rate something from 1-10"
        }
        
        self.jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs!",
            "How many programmers does it take to change a light bulb? None, that's a hardware problem!",
            "Why do Java developers wear glasses? Because they don't C#!",
            "What's a programmer's favorite hangout place? Foo Bar!",
            "Why did the developer go broke? Because he used up all his cache!",
            "What do you call a programmer from Finland? Nerdic!",
            "Why do Python programmers prefer snakes? Because they come with built-in scales!",
            "A SQL query goes into a bar, walks up to two tables and asks: 'Can I join you?'",
            "Why was the JavaScript developer sad? Because they didn't know how to 'null' their feelings!",
            "There are only 10 types of people: those who understand binary and those who don't."
        ]
        
        self.eight_ball_responses = [
            "It is certain ✨",
            "Without a doubt 👍",
            "Yes, definitely 💯",
            "You may rely on it 🎯",
            "Most likely 📈",
            "Outlook good 🌟",
            "Yes ✅",
            "Signs point to yes 👌",
            "Reply hazy, try again 🌫️",
            "Ask again later ⏰",
            "Better not tell you now 🤐",
            "Cannot predict now 🔮",
            "Concentrate and ask again 🧘",
            "Don't count on it ❌",
            "My reply is no 👎",
            "My sources say no 📰",
            "Outlook not so good 📉",
            "Very doubtful 🤔"
        ]
    
    def register_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/joke'))
        async def joke_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            self.bot.commands_processed += 1
            joke = random.choice(self.jokes)
            await event.reply(f"😄 **Programmer Joke:**\n\n{joke}")
        
        @self.bot.on(events.NewMessage(pattern='/dice'))
        async def dice_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            self.bot.commands_processed += 1
            result = random.randint(1, 6)
            dice_emoji = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"][result - 1]
            await event.reply(f"{dice_emoji} **You rolled a {result}!**")
        
        @self.bot.on(events.NewMessage(pattern='/coin'))
        async def coin_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            self.bot.commands_processed += 1
            result = random.choice(["Heads", "Tails"])
            emoji = "🪙" if result == "Heads" else "🔄"
            await event.reply(f"{emoji} **{result}!**")
        
        @self.bot.on(events.NewMessage(pattern='/8ball (.+)'))
        async def eight_ball_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            self.bot.commands_processed += 1
            question = event.pattern_match.group(1)
            response = random.choice(self.eight_ball_responses)
            await event.reply(
                f"🎱 **Magic 8-Ball**\n\n"
                f"**Q:** {question}\n"
                f"**A:** {response}",
                parse_mode='md'
            )
        
        @self.bot.on(events.NewMessage(pattern='/choose (.+)'))
        async def choose_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            self.bot.commands_processed += 1
            options = event.pattern_match.group(1).split(',')
            options = [opt.strip() for opt in options if opt.strip()]
            
            if len(options) < 2:
                await event.reply("❌ Please provide at least 2 options separated by commas!")
                return
            
            choice = random.choice(options)
            await event.reply(
                f"🎯 **Random Choice**\n\n"
                f"Options: {', '.join(options)}\n"
                f"**I choose:** __{choice}__",
                parse_mode='md'
            )
        
        @self.bot.on(events.NewMessage(pattern='/rate (.+)'))
        async def rate_handler(event):
            if await self.bot.check_rate_limit(event):
                return
            self.bot.commands_processed += 1
            thing = event.pattern_match.group(1)
            rating = random.randint(1, 10)
            
            # Add fun comments based on rating
            if rating <= 3:
                comment = "Not great... 😬"
            elif rating <= 5:
                comment = "It's okay I guess 🤷"
            elif rating <= 7:
                comment = "Pretty good! 👍"
            elif rating <= 9:
                comment = "Excellent! 🌟"
            else:
                comment = "PERFECT! 💯🔥"
            
            stars = "⭐" * rating + "☆" * (10 - rating)
            
            await event.reply(
                f"📊 **Rating for:** {thing}\n\n"
                f"{stars}\n"
                f"**Score:** {rating}/10\n"
                f"_{comment}_",
                parse_mode='md'
            )
