"""Configuration management for Xtension Bot"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Bot configuration from environment variables"""
    
    # Required settings
    bot_token: str
    
    # Optional API credentials
    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    
    # Session settings
    session_type: str = "sqlite"
    session_name: str = "xtension_bot"
    session_dir: str = "sessions"
    
    # Feature flags
    enable_plugins: bool = True
    
    # Directory settings
    plugin_dir: str = "plugins"
    data_dir: str = "data"
    
    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def from_environment(cls):
        """Create config from environment variables"""
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get API credentials
        api_id = os.getenv("API_ID")
        api_hash = os.getenv("API_HASH")
        
        # Convert API_ID to int if provided
        if api_id:
            try:
                api_id = int(api_id)
            except ValueError:
                api_id = None
        
        return cls(
            bot_token=os.getenv("BOT_TOKEN", ""),
            api_id=api_id,
            api_hash=api_hash,
            session_type=os.getenv("SESSION_TYPE", "sqlite").lower(),
            session_name=os.getenv("SESSION_NAME", "xtension_bot"),
            session_dir=os.getenv("SESSION_DIR", "sessions"),
            enable_plugins=os.getenv("ENABLE_PLUGINS", "true").lower() in ("true", "1", "yes"),
            plugin_dir=os.getenv("PLUGIN_DIR", "plugins"),
            data_dir=os.getenv("DATA_DIR", "data"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
    
    def validate(self):
        """Validate the configuration"""
        if not self.bot_token:
            print("❌ Error: BOT_TOKEN is required")
            print("Please set BOT_TOKEN in your .env file or environment")
            return False
        
        if self.session_type not in ("sqlite", "memory"):
            print(f"❌ Error: Invalid SESSION_TYPE: {self.session_type}")
            print("Valid options: sqlite, memory")
            return False
        
        return True
    
    def get_api_credentials(self):
        """Get API credentials, using defaults if not provided"""
        if self.api_id and self.api_hash:
            return self.api_id, self.api_hash
        
        # Default Telegram bot API credentials
        # These are publicly available for bot usage
        return 6, "eb06d4abfb49dc3eeb1aeb98ae0f581e"
