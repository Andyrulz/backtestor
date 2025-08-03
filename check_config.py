"""Utility to check and configure Kite app redirect URI."""

import os
from pathlib import Path
from src.config import KiteConfig

def check_kite_configuration():
    """Check current Kite configuration and provide setup instructions."""
    print("🔍 Kite App Configuration Checker")
    print("=" * 40)
    
    try:
        config = KiteConfig.from_env()
        print(f"✅ API Key: {config.api_key}")
        print(f"✅ API Secret: {'*' * len(config.api_secret)}")
        if config.access_token:
            print(f"✅ Access Token: {config.access_token[:20]}...")
        else:
            print("⚠️ No access token (this is normal if not authenticated yet)")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    print("\n🎯 Required Redirect URI Configuration:")
    print("=" * 45)
    print("For automatic token capture to work, your Kite app MUST be configured with:")
    print()
    print("📍 Redirect URI: http://localhost:3456/store_tokens")
    print()
    print("🔧 How to configure this:")
    print("1. Go to https://kite.trade/")
    print("2. Login to your account")
    print("3. Go to 'Console' -> 'API'")
    print("4. Find your app or create a new one")
    print("5. Set the Redirect URI to: http://localhost:3456/store_tokens")
    print("6. Save the configuration")
    print()
    print("⚠️ Important Notes:")
    print("• The redirect URI must be EXACTLY: http://localhost:3456/store_tokens")
    print("• Do not include any trailing slashes")
    print("• Make sure port 3456 is not blocked by firewall")
    print("• The app will start a local server on this port")
    
    print("\n🚀 Testing Automatic Capture:")
    print("=" * 35)
    print("After configuring the redirect URI, you can test with:")
    print("python test_redirect.py")
    
    return True

def create_env_template():
    """Create a template .env file if it doesn't exist."""
    env_path = Path(__file__).parent / ".env"
    
    if env_path.exists():
        print(f"✅ .env file already exists at: {env_path}")
        return
    
    template = """# Kite API Configuration
# Replace these with your actual Kite API credentials from https://kite.trade/

KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
KITE_ACCESS_TOKEN=

# Optional: Debug mode
DEBUG=false

# IMPORTANT: Configure your Kite app with this redirect URI:
# http://localhost:3456/store_tokens
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(template)
        print(f"✅ Created .env template at: {env_path}")
        print("📝 Please edit this file with your actual API credentials")
    except Exception as e:
        print(f"❌ Failed to create .env template: {e}")

if __name__ == "__main__":
    print("🛠️ Kite Trading System Setup")
    print("=" * 30)
    
    # Check if .env exists
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("⚠️ No .env file found")
        create_env_template()
        print("\n🔧 Please configure your .env file first, then run this again")
        exit(1)
    
    print()
    check_kite_configuration()
    
    print("\n💡 Next Steps:")
    print("1. Ensure your Kite app redirect URI is configured correctly")
    print("2. Run: python test_redirect.py (to test automatic capture)")
    print("3. Run your main app: streamlit run src/app.py")
    print("4. Enjoy automatic authentication! 🎉")
