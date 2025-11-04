"""Configuration loader for Xtension Bot"""

import os
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class Config:
    bot_token: str
    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    session_type: str = "sqlite"
    session_name: str = "bot"
    plugin_dir: str = "plugins"
    data_dir: str = "data"
    session_dir: str = "sessions"
    log_level: str = "INFO"
    debug: bool = False
    enable_plugins: bool = True
    auto_load_plugins: List[str] = field(default_factory=list)

    @classmethod
    def from_environment(cls) -> "Config":
        try:
            from dotenv import load_dotenv
            if Path(".env").exists():
                load_dotenv()
        except Exception:
            pass

        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN is required. Set it in .env or environment.")
        api_id = os.getenv("API_ID")
        if api_id:
            try:
                api_id = int(api_id)
            except ValueError:
                api_id = None

        auto_load = []
        if os.getenv("AUTO_LOAD_PLUGINS"):
            auto_load = [p.strip() for p in os.getenv("AUTO_LOAD_PLUGINS").split(",") if p.strip()]

        return cls(
            bot_token=bot_token,
            api_id=api_id,
            api_hash=os.getenv("API_HASH"),
            session_type=os.getenv("SESSION_TYPE", "sqlite"),
            session_name=os.getenv("SESSION_NAME", "bot"),
            plugin_dir=os.getenv("PLUGIN_DIR", "plugins"),
            data_dir=os.getenv("DATA_DIR", "data"),
            session_dir=os.getenv("SESSION_DIR", "sessions"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            debug=os.getenv("DEBUG", "false").lower() in ("true","1","yes"),
            enable_plugins=os.getenv("ENABLE_PLUGINS", "true").lower() in ("true","1","yes"),
            auto_load_plugins=auto_load
        )

    def validate(self) -> bool:
        if not self.bot_token or ":" not in self.bot_token:
            logger.error("Invalid BOT_TOKEN format")
            return False
        for d in [self.plugin_dir, self.data_dir, self.session_dir]:
            Path(d).mkdir(parents=True, exist_ok=True)
        return True

    def get_api_credentials(self):
    	if self.api_id and self.api_hash:
        	return self.api_id, self.api_hash
    # Use Telegram's official test credentials for bots
    	return 2899, "36722c72256a24c1225de00eb6a1ca74"
