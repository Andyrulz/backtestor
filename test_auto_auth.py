#!/usr/bin/env python3
"""Test the automated authentication system."""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from config import AppConfig
from auto_auth import AutoKiteAuth, get_auto_authenticated_client

def test_auto_auth():
    """Test the auto authentication system."""
    
    print("🔍 Testing Auto Authentication System...")
    print("=" * 50)
    
    try:
        # Load configuration
        config = AppConfig.from_env()
        print(f"✅ Configuration loaded")
        print(f"   API Key: {config.kite.api_key[:10]}...")
        print(f"   API Secret: {config.kite.api_secret[:10]}...")
        print(f"   Access Token: {config.kite.access_token[:10]}..." if config.kite.access_token else "   Access Token: Not set")
        print()
        
        # Test auto authentication
        auth = AutoKiteAuth(config.kite)
        
        print("🔐 Checking token validity...")
        if auth.is_token_valid():
            print("✅ Current token is valid!")
            
            # Test client creation
            client = get_auto_authenticated_client(config.kite)
            if client:
                profile = client.profile()
                print(f"👤 User: {profile.get('user_name', 'Unknown')}")
                print(f"📧 Email: {profile.get('email', 'N/A')}")
                print(f"🆔 User ID: {profile.get('user_id', 'N/A')}")
                print()
                print("🎉 Auto authentication system is working perfectly!")
                return True
            else:
                print("❌ Failed to create authenticated client")
                
        else:
            print("⚠️ Current token is invalid or expired")
            print("💡 Manual login will be required in the app")
            print()
            print("📋 To fix this:")
            print("1. Run: streamlit run src\\app.py")
            print("2. Complete the one-time login process")
            print("3. Token will be saved for 24 hours")
            
        return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_auto_auth()
