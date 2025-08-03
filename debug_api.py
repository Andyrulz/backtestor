"""Debug script to check API key and token configuration."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import KiteConfig
from kiteconnect import KiteConnect
import os

def debug_api_configuration():
    """Debug the API configuration and test connectivity."""
    print("🔍 API Configuration Debug")
    print("=" * 30)
    
    try:
        # Load configuration
        config = KiteConfig.from_env()
        
        print(f"✅ API Key: {config.api_key}")
        print(f"✅ API Secret: {'*' * len(config.api_secret)}")
        print(f"✅ Access Token: {config.access_token[:20] if config.access_token else 'None'}...")
        print()
        
        # Test 1: Check if API key format looks correct
        print("🧪 Test 1: API Key Format")
        if len(config.api_key) == 16 and config.api_key.isalnum():
            print("✅ API key format looks correct")
        else:
            print("❌ API key format might be incorrect")
            print(f"   Length: {len(config.api_key)} (should be 16)")
            print(f"   Alphanumeric: {config.api_key.isalnum()}")
        print()
        
        # Test 2: Check if access token format looks correct
        print("🧪 Test 2: Access Token Format")
        if config.access_token:
            if len(config.access_token) == 32 and config.access_token.isalnum():
                print("✅ Access token format looks correct")
            else:
                print("⚠️ Access token format might be incorrect")
                print(f"   Length: {len(config.access_token)} (should be 32)")
                print(f"   Alphanumeric: {config.access_token.isalnum()}")
        else:
            print("❌ No access token found")
        print()
        
        # Test 3: Try to create KiteConnect instance
        print("🧪 Test 3: KiteConnect Instance")
        try:
            kite = KiteConnect(api_key=config.api_key)
            print("✅ KiteConnect instance created successfully")
        except Exception as e:
            print(f"❌ Failed to create KiteConnect instance: {e}")
            return False
        print()
        
        # Test 4: Try to set access token
        print("🧪 Test 4: Setting Access Token")
        try:
            kite.set_access_token(config.access_token)
            print("✅ Access token set successfully")
        except Exception as e:
            print(f"❌ Failed to set access token: {e}")
            return False
        print()
        
        # Test 5: Try to get profile (this will test actual API connectivity)
        print("🧪 Test 5: API Connectivity Test")
        try:
            profile = kite.profile()
            print("✅ Successfully connected to Kite API!")
            print(f"   User ID: {profile.get('user_id', 'Unknown')}")
            print(f"   User Name: {profile.get('user_name', 'Unknown')}")
            print(f"   Email: {profile.get('email', 'Unknown')}")
            return True
        except Exception as e:
            print(f"❌ API connectivity failed: {e}")
            
            # Provide specific error analysis
            error_str = str(e).lower()
            if "invalid" in error_str and "api_key" in error_str:
                print("\n💡 Possible Issues:")
                print("   1. API key might be incorrect")
                print("   2. Access token might be expired or invalid")
                print("   3. API key and access token might be from different apps")
                print("\n🔧 Solutions:")
                print("   1. Verify API key in Kite Console (https://kite.trade/)")
                print("   2. Generate a new access token by re-authenticating")
                print("   3. Ensure API key and secret are from the same Kite app")
            
            return False
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def check_env_file():
    """Check if .env file has the correct format."""
    print("\n📁 .env File Check")
    print("=" * 20)
    
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found")
        return False
    
    try:
        with open(env_path, 'r') as f:
            content = f.read()
        
        print("✅ .env file found")
        
        # Check for required keys
        required_keys = ['KITE_API_KEY', 'KITE_API_SECRET', 'KITE_ACCESS_TOKEN']
        for key in required_keys:
            if f"{key}=" in content:
                print(f"✅ {key} found in .env")
            else:
                print(f"❌ {key} missing from .env")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def suggest_solutions():
    """Suggest solutions based on the debug results."""
    print("\n🛠️ Troubleshooting Steps")
    print("=" * 25)
    print("1. 🔐 Re-authenticate to get a fresh token:")
    print("   - Run the app and go through login again")
    print("   - This will generate a new access token")
    print()
    print("2. ✅ Verify Kite App Configuration:")
    print("   - Go to https://kite.trade/ → Console → API")
    print("   - Check your app's API key")
    print("   - Ensure redirect URI is: http://localhost:3456/store_tokens")
    print()
    print("3. 🔄 Check token freshness:")
    print("   - Kite tokens expire after 24 hours")
    print("   - You may need to authenticate daily")
    print()
    print("4. 🧪 Test with fresh authentication:")
    print("   - Delete the current token from .env")
    print("   - Run the app and authenticate again")

if __name__ == "__main__":
    print("🔧 Kite API Debug Tool")
    print("=" * 25)
    
    # Check environment file
    env_ok = check_env_file()
    
    if env_ok:
        # Debug API configuration
        api_ok = debug_api_configuration()
        
        if not api_ok:
            suggest_solutions()
        else:
            print("\n🎉 All tests passed! API configuration is working correctly.")
    else:
        print("\n❌ Environment file issues detected. Please fix .env file first.")
    
    print("\n" + "=" * 50)
