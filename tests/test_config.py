"""Tests for configuration module."""

import pytest
from unittest.mock import patch
from src.config import KiteConfig, AppConfig


class TestKiteConfig:
    """Test cases for KiteConfig."""
    
    @patch.dict("os.environ", {"KITE_API_KEY": "test_key", "KITE_ACCESS_TOKEN": "test_token"})
    def test_from_env_success(self):
        """Test successful configuration from environment variables."""
        config = KiteConfig.from_env()
        
        assert config.api_key == "test_key"
        assert config.access_token == "test_token"
    
    @patch.dict("os.environ", {}, clear=True)
    def test_from_env_missing_api_key(self):
        """Test configuration failure when API key is missing."""
        with pytest.raises(ValueError, match="KITE_API_KEY environment variable is required"):
            KiteConfig.from_env()
    
    @patch.dict("os.environ", {"KITE_API_KEY": "test_key"}, clear=True)
    def test_from_env_missing_access_token(self):
        """Test configuration failure when access token is missing."""
        with pytest.raises(ValueError, match="KITE_ACCESS_TOKEN environment variable is required"):
            KiteConfig.from_env()


class TestAppConfig:
    """Test cases for AppConfig."""
    
    @patch.dict("os.environ", {
        "KITE_API_KEY": "test_key", 
        "KITE_ACCESS_TOKEN": "test_token",
        "DEBUG": "true"
    })
    def test_from_env_with_debug(self):
        """Test app configuration with debug enabled."""
        config = AppConfig.from_env()
        
        assert config.kite.api_key == "test_key"
        assert config.kite.access_token == "test_token"
        assert config.debug is True
    
    @patch.dict("os.environ", {
        "KITE_API_KEY": "test_key", 
        "KITE_ACCESS_TOKEN": "test_token"
    })
    def test_from_env_default_debug(self):
        """Test app configuration with default debug setting."""
        config = AppConfig.from_env()
        
        assert config.debug is False
