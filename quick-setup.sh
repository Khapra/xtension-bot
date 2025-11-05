#!/bin/bash
# Xtension Bot v1.2.0 - Quick Docker Setup
# No code download required!

echo "╔══════════════════════════════════════════╗"
echo "║     🚀 XTENSION BOT v1.2.0 SETUP 🚀      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo "👉 Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Get configuration
echo "📋 Configuration"
echo "────────────────"
read -p "🔑 Bot Token (@BotFather): " BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ Bot token is required!"
    exit 1
fi

echo "💡 Optional: Get your ID from @userinfobot"
read -p "👤 Your Telegram ID (or press Enter): " ADMIN_ID

# Create docker-compose.yml
cat > docker-compose.yml <<EOL
version: '3.8'

services:
  xtension-bot:
    image: khapra/xtension-bot:latest
    container_name: xtension-bot
    environment:
      BOT_TOKEN: ${BOT_TOKEN}
      ADMIN_IDS: ${ADMIN_ID:-}
      LOG_LEVEL: INFO
      # Rate limiting (v1.1.1)
      RATE_LIMIT_PER_MINUTE: 30
      RATE_LIMIT_PER_HOUR: 300
    volumes:
      - ./bot_data:/app/sessions
      - ./plugins:/app/plugins:ro
    restart: unless-stopped
EOL

echo ""
echo "📦 Downloading bot..."
docker-compose pull

echo "🚀 Starting bot..."
docker-compose up -d

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Bot is running!"
    echo ""
    echo "📝 Commands:"
    echo "  Logs:    docker-compose logs -f"
    echo "  Stop:    docker-compose down"
    echo "  Update:  docker-compose pull && docker-compose up -d"
else
    echo "❌ Failed. Check Docker."
fi
