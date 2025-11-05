# 🤖 Xtension Bot

[![Version](https://img.shields.io/badge/version-1.1.1-blue.svg)](https://github.com/Khapra/xtension-bot)
[![GitHub](https://img.shields.io/badge/GitHub-Source-green.svg)](https://github.com/Khapra/xtension-bot)

A powerful, modular Telegram bot with hot-reloadable plugins, rate limiting, and production-ready architecture.

## 🚀 Quick Start

docker run -d \
  -e BOT_TOKEN="YOUR_BOT_TOKEN" \
  -e LOG_LEVEL="INFO" \
  --name xtension-bot \
  --restart unless-stopped \
  khapra/xtension-bot:latest

## 📦 With Persistence (Volumes)

docker run -d \
  -e BOT_TOKEN="YOUR_BOT_TOKEN" \
  -v $(pwd)/sessions:/app/sessions \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/plugins:/app/plugins:ro \
  --name xtension-bot \
  --restart unless-stopped \
  khapra/xtension-bot:latest

## 🐳 Docker Compose with Full Persistence

version: '3.8'
services:
  xtension-bot:
    image: khapra/xtension-bot:latest
    container_name: xtension-bot
    environment:
      BOT_TOKEN: YOUR_BOT_TOKEN
      ADMIN_IDS: YOUR_TELEGRAM_ID
      LOG_LEVEL: INFO
      RATE_LIMIT_PER_MINUTE: 30
      RATE_LIMIT_PER_HOUR: 300
    volumes:
      # Session data persistence
      - ./sessions:/app/sessions
      # Data persistence
      - ./data:/app/data
      # Custom plugins (read-only for safety)
      - ./custom_plugins:/app/plugins:ro
      # Optional: Bot logs
      - ./logs:/app/logs
    restart: unless-stopped

## 📁 Volume Mounts Explained

| Volume | Purpose | Mode |
|--------|---------|------|
| /app/sessions | Telegram session files | Read/Write |
| /app/data | Bot data & databases | Read/Write |
| /app/plugins | Custom plugins | Read-Only |
| /app/logs | Log files | Read/Write |

## ✨ Features

- 🔌 Plugin System - Hot-reloadable plugins
- 🛡️ Rate Limiting - Advanced spam protection
- 📊 Flexible Logging - DEBUG/INFO modes
- 🔐 Admin Controls - Full bot management
- ⚡ Fast & Lightweight - Built with Telethon
- 💾 Persistent Storage - Session & data preservation

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| BOT_TOKEN | Telegram Bot Token (Required) | - |
| ADMIN_IDS | Comma-separated admin IDs | - |
| LOG_LEVEL | Logging level | INFO |
| RATE_LIMIT_PER_MINUTE | Commands per minute | 30 |
| RATE_LIMIT_PER_HOUR | Commands per hour | 300 |

## 📚 Documentation

Full documentation: https://github.com/Khapra/xtension-bot

## 🏷️ Available Tags

- latest - Latest stable version
- v1.1.1 - Version 1.1.1
- main - Latest development build

## 🤝 Support

- GitHub Issues: https://github.com/Khapra/xtension-bot/issues
- Source Code: https://github.com/Khapra/xtension-bot

---

Created by @Khapra | MIT License
