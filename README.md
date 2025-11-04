# 🤖 Xtension Bot

A lightweight, extensible Telegram bot built with Telethon.

Quick structure:
- bot/ — core bot code
- plugins/ — drop-in plugin Python files
- docker-compose.yml, Dockerfile — for containerized deployment

Quick start (Mac):
1. Create project folder and files (use the provided heredoc commands).
2. Copy `.env.example` to `.env` and add your BOT_TOKEN.
3. Run `./run.sh` or `docker-compose up -d`.
4. View logs: `docker-compose logs -f`.

Core commands:
- /start — welcome
- /help — help text
- /ping — health check
- /plugins — list loaded plugins
