#!/bin/bash

# Xtension Bot Quick Start Script
echo "🚀 Starting Xtension Bot..."

# Try to find Python (python3 first, then python)
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Python is not installed"
    exit 1
fi

echo "📍 Using Python: $PYTHON_CMD"

# Check for .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your BOT_TOKEN"
    exit 1
fi

# Check if BOT_TOKEN is set
if ! grep -q "BOT_TOKEN=.*[a-zA-Z0-9]" .env; then
    echo "❌ BOT_TOKEN not configured in .env"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start bot with optional log level (default: INFO)
echo "✅ Starting bot..."
LOG_LEVEL=${1:-INFO} python -m bot
