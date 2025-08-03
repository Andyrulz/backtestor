#!/usr/bin/env python3
"""Debug the authentication flow."""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from config import KiteConfig
from auto_auth import AutoKiteAuth, get_auto_authenticated_client

def debug_auth():
    """Debug the authentication process."""
    try:
        # Load configuration
        config = KiteConfig.from_env()
        print(f"Config loaded:")
        print(f"  API Key: {config.api_key}")
        print(f"  Access Token: {config.access_token[:20]}..." if config.access_token else "  Access Token: None")
        
        # Test AutoKiteAuth
        auth = AutoKiteAuth(config)
        print(f"\nTesting AutoKiteAuth.is_token_valid()...")
        is_valid = auth.is_token_valid()
        print(f"  Result: {is_valid}")
        
        # Test get_auto_authenticated_client
        print(f"\nTesting get_auto_authenticated_client()...")
        client = get_auto_authenticated_client(config)
        print(f"  Result: {client is not None}")
        
        if client:
            print("  Testing client.profile()...")
            profile = client.profile()
            print(f"  Profile success: {profile.get('user_name')}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_auth()
