# 🤖 Xtension Bot v4.0.0

A powerful, extensible Telegram bot framework built with Telethon. Features a dynamic plugin system, Docker support, and production-ready architecture.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Telethon](https://img.shields.io/badge/telethon-1.36.0-green.svg)](https://github.com/LonamiWebs/Telethon)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## ✨ Features

- 🔌 **Dynamic Plugin System** - Hot-reload plugins without restarting
- 🐳 **Docker Ready** - One-command deployment with Docker Compose
- 📦 **Modular Architecture** - Clean separation of core and plugins
- 🔒 **Session Management** - SQLite/Memory session support
- 📝 **Comprehensive Logging** - Configurable log levels
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

### Option 3: Quick Run Script (macOS/Linux)

```bash
./run.sh
```

## 📁 Project Structure

```
xtension-bot/
├── bot/                    # Core bot module
│   ├── __init__.py        # Package initialization
│   ├── __main__.py        # Entry point
│   ├── config.py          # Configuration management
│   └── core.py            # Main bot implementation
├── plugins/               # Plugin directory
│   └── example.py         # Example plugin
├── sessions/              # Session storage (auto-created)
├── data/                  # Data storage (auto-created)
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose config
└── run.sh               # Quick start script
```

## ⚙️ Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ Yes | - | Bot token from @BotFather |
| `API_ID` | No | Auto | Telegram API ID |
| `API_HASH` | No | Auto | Telegram API Hash |
| `SESSION_TYPE` | No | sqlite | Session type (sqlite/memory) |
| `SESSION_NAME` | No | bot | Session file name |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `DEBUG` | No | false | Enable debug mode |
| `ENABLE_PLUGINS` | No | true | Enable plugin system |
| `AUTO_LOAD_PLUGINS` | No | - | Comma-separated plugin names to load |

## 🔌 Plugin Development

Plugins are Python files in the `plugins/` directory that follow this structure:

### Example Plugin

```python
from telethon import events

class TelethonPlugin:
    def __init__(self, bot):
        self.bot = bot
        
    def register_handlers(self):
        @self.bot.on(events.NewMessage(pattern='/mycommand'))
        async def my_command(event):
            await event.reply("Hello from my plugin!")
            
        @self.bot.on(events.NewMessage(pattern='/echo (.+)'))
        async def echo(event):
            text = event.pattern_match.group(1)
            await event.reply(f"Echo: {text}")
```

### Creating a New Plugin

1. Create a new `.py` file in `plugins/` directory
2. Define a `TelethonPlugin` class
3. Implement `register_handlers()` method
4. Add your event handlers
5. Bot will auto-load on startup (or restart bot)

## 📝 Built-in Commands

- `/start` - Welcome message with inline buttons
- `/help` - Show available commands
- `/ping` - Health check (responds with 🏓 Pong!)
- `/plugins` - List loaded plugins
- `/hello` - Example plugin command
- `/echo <text>` - Echo back text (example plugin)

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
```

## 📊 Health Monitoring

The Docker setup includes health checks that run every 30 seconds. Check status:

```bash
docker ps
docker inspect xtension-bot --format='{{.State.Health.Status}}'
```

## 🛠️ Development

### Run in Development Mode

```bash
# Set debug mode in .env
DEBUG=true
LOG_LEVEL=DEBUG

# Run with auto-reload (if using development tools)
python -m bot
```

### Testing Plugins

Place test plugins in `plugins/` directory. They're loaded automatically on bot startup.

### Project Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests (if available)
python -m pytest

# Format code
black bot/ plugins/

# Lint code
pylint bot/ plugins/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Bot not responding?
- Check bot token in `.env` is correct
- Ensure bot is not running elsewhere
- Check logs: `docker-compose logs` or console output

### Session errors?
- Delete `sessions/` folder and restart
- Try `SESSION_TYPE=memory` for testing

### Plugin not loading?
- Check plugin has `TelethonPlugin` class
- Verify `register_handlers()` method exists
- Check logs for error messages
- Ensure `ENABLE_PLUGINS=true` in `.env`

### Docker issues?
- Ensure Docker is running: `docker info`
- Check permissions: `sudo docker-compose up`
- Rebuild image: `docker-compose build --no-cache`

## 📚 Resources

- [Telethon Documentation](https://docs.telethon.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Docker Documentation](https://docs.docker.com/)
- [Python Async/Await](https://docs.python.org/3/library/asyncio.html)

## 👤 Author

**Khapra**
- GitHub: [@Khapra](https://github.com/Khapra)

## 🌟 Acknowledgments

- Built with [Telethon](https://github.com/LonamiWebs/Telethon)
- Inspired by modular bot architectures
- Thanks to the Telegram bot development community

---

**Current Version**: 1.0.1 | **Last Updated**: November 2025
