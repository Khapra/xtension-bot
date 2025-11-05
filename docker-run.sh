#!/bin/bash
echo "🚀 Xtension Bot - One Line Setup"
read -p "Bot Token: " TOKEN
docker run -d --name xtension-bot \
  -e BOT_TOKEN="$TOKEN" \
  -e LOG_LEVEL="INFO" \
  --restart unless-stopped \
  khapra/xtension-bot:latest
echo "✅ Running! Logs: docker logs -f xtension-bot"
