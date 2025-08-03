#!/usr/bin/env python3
"""Test the current access token validity."""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from config import KiteConfig
from kiteconnect import KiteConnect

def test_access_token():
    """Test if the current access token is valid."""
    try:
        # Load configuration
        config = KiteConfig.from_env()
        print(f"API Key: {config.api_key}")
        print(f"Access Token: {config.access_token[:20]}..." if config.access_token else "No access token found")
        
        if not config.access_token:
            print("❌ No access token found in .env file")
            return False
        
        # Test the token
        kite = KiteConnect(api_key=config.api_key)
        kite.set_access_token(config.access_token)
        
        print("🔄 Testing access token...")
        profile = kite.profile()
        
        print(f"✅ Access token is valid!")
        print(f"User ID: {profile.get('user_id')}")
        print(f"User Name: {profile.get('user_name')}")
        print(f"Email: {profile.get('email')}")
        return True
        
    except Exception as e:
        print(f"❌ Access token test failed: {e}")
        return False

if __name__ == "__main__":
    test_access_token()
