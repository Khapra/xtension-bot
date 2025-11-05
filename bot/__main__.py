"""Module entry point for Xtension Bot"""

import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.core import XtensionBot
from bot.config import Config

# Use LOG_LEVEL from environment
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    format='[%(asctime)s] %(levelname)-8s | %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=getattr(logging, log_level, logging.INFO)
)

async def main():
    config = Config.from_environment()
    if not config.validate():
        raise SystemExit(1)

    bot = XtensionBot(config)
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user")
