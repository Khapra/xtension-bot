# 🚀 INSTANT SETUP - NO DOWNLOADS REQUIRED!

Run Xtension Bot with just Docker - no Git, no Python needed!

## Quick Start (30 seconds!)

### Option 1: Simplest - One Command
```bash
docker run -d \
  -e BOT_TOKEN="YOUR_BOT_TOKEN_HERE" \
  -e LOG_LEVEL="INFO" \
  --name xtension-bot \
  --restart unless-stopped \
  khapra/xtension-bot:latest
```

### Option 2: Docker Compose
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  xtension-bot:
    image: khapra/xtension-bot:latest
    environment:
      BOT_TOKEN: YOUR_BOT_TOKEN_HERE
      ADMIN_IDS: YOUR_TELEGRAM_ID  # Optional
      LOG_LEVEL: INFO
    restart: unless-stopped
```
Then run: `docker-compose up -d`

### Option 3: Interactive Setup
```bash
curl -sSL https://raw.githubusercontent.com/Khapra/xtension-bot/main/quick-setup.sh | bash
```

## Management Commands
```bash
# View logs
docker logs -f xtension-bot

# Stop bot
docker stop xtension-bot

# Remove bot
docker rm xtension-bot

# Update to latest version
docker pull khapra/xtension-bot:latest
docker restart xtension-bot
```

---

# 🤖 Xtension Bot - Advanced Telegram Bot Framework

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/Khapra/xtension-bot/releases)
[![Docker](https://img.shields.io/docker/pulls/khapra/xtension-bot)](https://hub.docker.com/r/khapra/xtension-bot)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A powerful, modular Telegram bot built with Telethon featuring hot-reloadable plugins, rate limiting, and production-ready architecture.

## ✨ Features

- 🔌 **Plugin System** - Hot-reloadable plugins without restarting
- 🛡️ **Rate Limiting** - Advanced spam protection (v1.1.1)
- 📊 **Flexible Logging** - DEBUG/INFO modes for development and production
- 🐳 **Docker Support** - One-command deployment
- 🔐 **Admin Controls** - Comprehensive bot management
- ⚡ **Fast & Lightweight** - Built with Telethon for optimal performance
- 🎯 **Production Ready** - Enterprise-grade error handling

## 🚀 Installation Methods

### Method 1: Traditional Setup

1. **Clone the repository:**
```bash
git clone https://github.com/Khapra/xtension-bot.git
cd xtension-bot
```

2. **Set up virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your BOT_TOKEN
```

5. **Run the bot:**
```bash
python -m bot
```

### Method 2: Docker (Recommended)
See the Quick Start section above for Docker deployment.

## 📋 Configuration

### Environment Variables

Create a `.env` file with:

```env
# Required
BOT_TOKEN=your_bot_token_from_botfather

# Optional
ADMIN_IDS=123456789,987654321
LOG_LEVEL=INFO  # or DEBUG

# Rate Limiting (v1.1.1)
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=300
RATE_LIMIT_BURST=5
RATE_LIMIT_BURST_WINDOW=10
RATE_LIMIT_COOLDOWN=60
```

## 🎮 Commands

### Core Commands
- `/start` - Welcome message and bot info
- `/help` - List all available commands
- `/ping` - Check bot responsiveness
- `/stats` - View bot statistics (admin only)
- `/version` - Show bot version
- `/plugins` - Manage plugins (admin only)
- `/reload [plugin]` - Hot-reload plugins
- `/restart` - Restart the bot (admin only)
- `/logs [lines]` - View recent logs (admin only)
- `/ratelimit` - Manage rate limits (admin only)

### Fun Commands
- `/joke` - Get a random joke
- `/meme` - Generate a random meme
- `/8ball <question>` - Ask the magic 8-ball
- `/roll [sides]` - Roll a dice
- `/flip` - Flip a coin

### Info Commands
- `/info [user]` - Get user information
- `/chatinfo` - Get chat information
- `/userid` - Get your user ID
- `/time [timezone]` - Get current time

## 🔌 Plugin Development

Create custom plugins in the `plugins/` directory:

```python
# plugins/my_plugin.py
from bot.plugin_wrapper import PluginWrapper

plugin = PluginWrapper("MyPlugin")

@plugin.command("mycommand")
async def my_command(event):
    """Description of your command"""
    await event.reply("Hello from my plugin!")

def setup():
    return plugin
```

## 🛡️ Rate Limiting (v1.1.1)

Advanced rate limiting system to prevent spam:
- **Per-minute limit**: 30 commands (configurable)
- **Per-hour limit**: 300 commands (configurable)
- **Burst detection**: 5 commands in 10 seconds triggers cooldown
- **Admin bypass**: Admins are exempt from all limits
- **Auto-cooldown**: Automatic temporary bans for violators

## 📊 Monitoring

### View Logs
```bash
# Docker
docker logs -f xtension-bot

# Traditional
tail -f bot.log
```

### Bot Statistics
Use `/stats` command in Telegram (admin only) to see:
- Uptime and performance
- Total commands processed
- Active plugins
- Rate limit statistics
- Memory usage

## 🚀 Deployment

### Deploy to VPS/Cloud
```bash
# Using Docker (recommended)
docker run -d \
  -e BOT_TOKEN="your_token" \
  -e ADMIN_IDS="your_id" \
  --restart unless-stopped \
  khapra/xtension-bot:latest
```

### Deploy with docker-compose
```yaml
version: '3.8'
services:
  bot:
    image: khapra/xtension-bot:latest
    environment:
      BOT_TOKEN: ${BOT_TOKEN}
      ADMIN_IDS: ${ADMIN_IDS}
      LOG_LEVEL: INFO
    volumes:
      - ./data:/app/data
      - ./custom_plugins:/app/plugins:ro
    restart: unless-stopped
```

## 🔄 Updates

### Docker Update
```bash
docker pull khapra/xtension-bot:latest
docker restart xtension-bot
```

### Git Update
```bash
git pull origin main
pip install -r requirements.txt
# Restart bot
```

## 📈 Version History

- **v1.2.0** – Unified version file, dynamic versioning, Docker Compose-ready, plugins hot-reloadable
- **v1.1.1** - Rate limiting system, spam protection
- **v1.1.0** - Complete logging system, production ready
- **v1.0.0** - Initial release with plugin system

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Khapra**
- GitHub: [@Khapra](https://github.com/Khapra)
- Docker Hub: [khapra/xtension-bot](https://hub.docker.com/r/khapra/xtension-bot)

## 🙏 Acknowledgments

- Built with [Telethon](https://github.com/LonamiWebs/Telethon)
- Inspired by the Telegram bot community

## 📞 Support

- Create an issue on [GitHub](https://github.com/Khapra/xtension-bot/issues)
- Check [Discussions](https://github.com/Khapra/xtension-bot/discussions)

---

**Current Version:** See [VERSION](./VERSION)   
**Status:** 🟢 Production Ready  
**Docker:** `docker pull khapra/xtension-bot:latest`


<!-- Docker Hub: https://hub.docker.com/r/khapra/xtension-bot -->
