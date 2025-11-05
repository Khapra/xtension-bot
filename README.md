# 🤖 Xtension Bot v1.1.0

A powerful, extensible Telegram bot framework built with Telethon. Features a dynamic plugin system with automatic command discovery, comprehensive logging, Docker support, and production-ready architecture.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Telethon](https://img.shields.io/badge/telethon-1.36.0-green.svg)](https://github.com/LonamiWebs/Telethon)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Version](https://img.shields.io/badge/version-1.1.0-orange.svg)](https://github.com/Khapra/xtension-bot/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## ✨ What's New in v1.1.0 (2025-11-05)

- 🎯 **Dynamic Command Discovery** - Plugins self-declare their commands
- 📊 **Automatic Plugin Logging** - All plugin commands logged in DEBUG mode
- 🔐 **Built-in Admin System** - Core admin commands with role-based access
- 📈 **Enhanced Statistics** - Command counter, uptime, memory usage
- 🔄 **Improved Plugin Reload** - Clean hot-reload without loops
- 📝 **Unified Logging System** - Single LOG_LEVEL variable for all logging
- 🎨 **Better UI/UX** - Improved command formatting and responses

## ⭐ Features

- 🔌 **Dynamic Plugin System** - Drop-in Python files that auto-register commands
- 🤖 **Smart Command Discovery** - Commands automatically detected from plugins
- 📊 **Comprehensive Logging** - Multi-level logging system (DEBUG/INFO/WARNING/ERROR)
- 🐳 **Docker Ready** - One-command deployment with Docker Compose
- 📦 **Modular Architecture** - Clean separation of core and plugins
- 🔒 **Admin Controls** - Built-in admin commands for bot management
- ⚡ **Async/Await** - Built on Telethon's async framework
- 🛠️ **Easy Configuration** - Simple .env file setup
- 🎯 **Production Ready** - Health checks, auto-restart, error handling

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ OR Docker
- Telegram Bot Token from [@BotFather](https://t.me/botfather)

### Option 1: Run with Python

```bash
# Clone repository
git clone https://github.com/Khapra/xtension-bot.git
cd xtension-bot

# Setup environment
cp .env.example .env
# Edit .env and add your BOT_TOKEN

# Install and run
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m bot
```

### Option 2: Run with Docker

```bash
# Clone repository
git clone https://github.com/Khapra/xtension-bot.git
cd xtension-bot

# Setup environment
cp .env.example .env
# Edit .env and add your BOT_TOKEN

# Run with Docker Compose
docker-compose up -d
docker-compose logs -f
```

## 📁 Project Structure

```
xtension-bot/
├── bot/                    # Core bot module
│   ├── __init__.py        # Package initialization
│   ├── __main__.py        # Entry point
│   ├── config.py          # Configuration management
│   ├── core.py            # Main bot implementation
│   └── plugin_wrapper.py  # Plugin logging utilities (v1.1.0)
├── plugins/               # Plugin directory
│   ├── example.py         # Example plugin with command structure
│   ├── info.py           # System information plugin
│   └── fun.py            # Entertainment commands plugin
├── sessions/              # Session storage (auto-created)
├── data/                  # Data storage (auto-created)
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose config
├── run.sh               # Quick start script
└── README.md            # This file
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ Yes | - | Bot token from @BotFather |
| `ADMIN_IDS` | No | - | Comma-separated Telegram user IDs for admins |
| `API_ID` | No | Auto | Telegram API ID (optional for bots) |
| `API_HASH` | No | Auto | Telegram API Hash (optional for bots) |
| `SESSION_TYPE` | No | sqlite | Session type (sqlite/memory) |
| `SESSION_NAME` | No | xtension_bot | Session file name |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `ENABLE_PLUGINS` | No | true | Enable plugin system |
| `PLUGIN_DIR` | No | plugins | Plugin directory path |
| `DATA_DIR` | No | data | Data storage directory |
| `SESSION_DIR` | No | sessions | Session storage directory |

### Getting Admin ID
1. Search for `@userinfobot` on Telegram
2. Start the bot to get your user ID
3. Add it to `.env`: `ADMIN_IDS=your_id_here`

## 🔧 Logging Modes

### INFO Mode (Production)
```bash
LOG_LEVEL=INFO python -m bot
```
Shows:
- Bot startup/shutdown
- Plugin loading status
- Major events only
- Clean, minimal output

### DEBUG Mode (Development)
```bash
LOG_LEVEL=DEBUG python -m bot
```
Shows everything including:
- All commands executed with user info
- Plugin command tracking `[PLUGIN:name]`
- Admin permission checks
- Detailed error traces
- Handler registration
- Module loading/unloading

### Other Log Levels
```bash
LOG_LEVEL=WARNING python -m bot  # Only warnings and errors
LOG_LEVEL=ERROR python -m bot    # Only errors
```

## 🔌 Plugin Development

### Plugin Structure (v1.1.0)

```python
from telethon import events

class TelethonPlugin:
    def __init__(self, bot):
        self.bot = bot
        # Define commands with descriptions
        self.commands = {
            "/mycommand": "Description of what this command does",
            "/another <arg>": "Command with argument"
        }
        
    def register_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/mycommand'))
        async def my_command(event):
            await event.reply("Response from my command!")
            
        @self.bot.on(events.NewMessage(pattern='/another (.+)'))
        async def another(event):
            arg = event.pattern_match.group(1)
            await event.reply(f"You said: {arg}")
```

### Creating a New Plugin

1. Create a new `.py` file in `plugins/` directory
2. Define a `TelethonPlugin` class
3. Add `commands` dictionary in `__init__`
4. Implement `register_handlers()` method
5. Reload plugins with `/reload` (admin command)

### Example Plugin

```python
# plugins/weather.py
from telethon import events
import random

class TelethonPlugin:
    def __init__(self, bot):
        self.bot = bot
        self.commands = {
            "/weather <city>": "Get weather for a city (demo)",
            "/forecast": "Get weather forecast (demo)"
        }
    
    def register_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/weather (.+)'))
        async def weather(event):
            city = event.pattern_match.group(1)
            temp = random.randint(15, 30)
            conditions = random.choice(["☀️ Sunny", "☁️ Cloudy", "🌧️ Rainy"])
            await event.reply(f"Weather in {city}: {temp}°C, {conditions}")
        
        @self.bot.on(events.NewMessage(pattern='/forecast'))
        async def forecast(event):
            await event.reply("🌤️ This week: Partly cloudy with a chance of code!")
```

## 📝 Built-in Commands

### Core Commands (Available to all users)
| Command | Description |
|---------|-------------|
| `/start` | Show welcome message and bot information |
| `/help` | Display all available commands |
| `/ping` | Check if bot is responsive |
| `/plugins` | List loaded plugins with command counts |
| `/version` | Show bot version, uptime, and stats |

### Admin Commands (Restricted)
| Command | Description |
|---------|-------------|
| `/reload` | Hot-reload all plugins without restart |
| `/restart` | Restart the bot process completely |
| `/shutdown` | Stop the bot |
| `/stats` | Detailed bot statistics and system info |

### Default Plugins

**Example Plugin:**
- `/hello` - Simple greeting
- `/echo <text>` - Echo your message
- `/bold <text>` - Make text bold
- `/italic <text>` - Make text italic

**Info Plugin:**
- `/info` - Bot and system information
- `/sysinfo` - Detailed system stats
- `/botinfo` - Bot-specific details

**Fun Plugin:**
- `/joke` - Random programmer joke
- `/dice` - Roll a dice (1-6)
- `/coin` - Flip a coin
- `/8ball <question>` - Magic 8-ball
- `/choose <options>` - Random choice maker
- `/rate <thing>` - Rate something randomly

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t xtension-bot .

# Run container
docker run -d \
  --name xtension-bot \
  --env-file .env \
  -v ./sessions:/app/sessions \
  -v ./data:/app/data \
  -v ./plugins:/app/plugins:ro \
  xtension-bot
```

### Docker Compose

```bash
# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart

# Update and restart
docker-compose pull
docker-compose up -d
```

## 📊 Health Monitoring

The Docker setup includes health checks that run every 30 seconds:

```bash
# Check status
docker ps

# Check health
docker inspect xtension-bot --format='{{.State.Health.Status}}'

# View recent logs
docker logs xtension-bot --tail 50 -f
```

## 🛠️ Development

### Testing Plugins

1. Create plugin in `plugins/` directory
2. Use `/reload` command to load without restart
3. Test commands immediately
4. Check `/help` to see new commands listed
5. Use DEBUG mode to see command execution logs

### Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run with debug logging
LOG_LEVEL=DEBUG python -m bot

# Check what will be committed (security check)
git status

# Format code
black bot/ plugins/

# Lint code
pylint bot/ plugins/

# Run tests (if available)
pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Follow the plugin structure for new plugins
4. Test in DEBUG mode to verify logging
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing`)
7. Open a Pull Request

### Contribution Guidelines
- Follow the existing code style
- Add logging for debugging
- Update documentation
- Test thoroughly before submitting
- One feature per pull request

## 🔒 Security

- **Never commit `.env` file** - Use `.env.example` as template
- Session files are automatically gitignored
- Use environment variables for sensitive data
- Admin IDs restrict dangerous commands
- DEBUG mode should only be used in development
- Regularly update dependencies for security patches

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Bot not responding?
- Check bot token in `.env` is correct
- Ensure bot is not running elsewhere
- Check logs: `docker-compose logs` or console output
- Verify bot has been started with `/start` in @BotFather

### Plugin not loading?
- Check plugin has `TelethonPlugin` class
- Verify `commands` dictionary exists
- Ensure `register_handlers()` method exists
- Run in DEBUG mode to see detailed errors
- Check file permissions in plugins directory

### Commands not showing in help?
- Ensure plugin has `commands` dictionary
- Commands must be defined in `__init__`
- Use `/reload` after adding new commands
- Check for syntax errors in plugin

### No plugin command logs in DEBUG mode?
- Ensure `LOG_LEVEL=DEBUG` is set
- Plugin must be loaded after debug mode starts
- Check for `[PLUGIN:name]` tags in output
- Verify plugin_wrapper.py exists

## 📚 Resources

- [Telethon Documentation](https://docs.telethon.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Plugin Examples](plugins/)
- [Docker Documentation](https://docs.docker.com/)
- [Python Async/Await](https://docs.python.org/3/library/asyncio.html)

## 🔄 Version History

### v1.1.0 (2025-11-05)
- Added automatic plugin command logging
- Implemented unified LOG_LEVEL system
- Dynamic command discovery from plugins
- Built-in admin system in core
- Plugin wrapper for universal logging
- Enhanced statistics with command counter
- Improved error handling and debugging
- Added comprehensive `.gitignore`
- Fixed plugin reload loops
- Better command descriptions

### v1.0.0 (2025-11-04)
- Initial release
- Basic plugin system
- Docker support
- Core commands

## 🚀 Roadmap

- [ ] Database integration (SQLite/PostgreSQL)
- [ ] Web dashboard for monitoring
- [ ] Plugin marketplace
- [ ] Automated testing suite
- [ ] Multi-language support
- [ ] Webhook mode support
- [ ] Rate limiting system
- [ ] Plugin dependencies management

## 👤 Author

**Khapra**
- GitHub: [@Khapra](https://github.com/Khapra)
- Repository: [xtension-bot](https://github.com/Khapra/xtension-bot)
- Released: November 5, 2025

## 🌟 Acknowledgments

- Built with [Telethon](https://github.com/LonamiWebs/Telethon)
- Inspired by modular bot architectures
- Special thanks to Claude Opus 4.1 for development assistance

---

**Current Version**: 1.1.0 | **Released**: 2025-11-05 | **Status**: Production Ready

For updates and releases, visit the [GitHub repository](https://github.com/Khapra/xtension-bot).
