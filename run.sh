#!/bin/bash
# Quick run script for macOS

set -e

if [ ! -f .env ]; then
  echo ".env not found. Copying from .env.example"
  cp .env.example .env
  echo "Edit .env and set BOT_TOKEN, then run ./run.sh again"
  exit 1
fi

# Start with Docker Compose
docker-compose up -d
docker-compose logs -f
