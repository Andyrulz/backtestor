"""Configuration management for the Kite trading system."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file in the project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


@dataclass
class KiteConfig:
    """Configuration for Kite API connection."""
    
    api_key: str
    api_secret: str
    access_token: str = ""
    
    @classmethod
    def from_env(cls) -> "KiteConfig":
        """Create configuration from environment variables.
        
        Returns:
            KiteConfig: Configuration instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        api_key = os.getenv("KITE_API_KEY")
        api_secret = os.getenv("KITE_API_SECRET")
        access_token = os.getenv("KITE_ACCESS_TOKEN", "")
        
        if not api_key:
            raise ValueError("KITE_API_KEY environment variable is required")
        if not api_secret:
            raise ValueError("KITE_API_SECRET environment variable is required")
            
        return cls(api_key=api_key, api_secret=api_secret, access_token=access_token)


@dataclass
class AppConfig:
    """Application configuration."""
    
    kite: KiteConfig
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create application configuration from environment variables.
        
        Returns:
            AppConfig: Application configuration instance
        """
        kite_config = KiteConfig.from_env()
        debug = os.getenv("DEBUG", "false").lower() == "true"
        
        return cls(kite=kite_config, debug=debug)
