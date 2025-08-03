"""Test script to verify the caching fix works."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import AppConfig
from streamlit_auth import get_streamlit_authenticated_client
from kite.client import KiteClient

def test_client_creation():
    """Test that the client is created correctly with fresh config."""
    print("🧪 Testing Client Creation with Fresh Config")
    print("=" * 45)
    
    try:
        # Load config fresh
        config = AppConfig.from_env()
        print(f"✅ Config loaded - API Key: {config.kite.api_key}")
        print(f"✅ Access Token: {config.kite.access_token[:20]}...")
        
        # Get authenticated client
        kite_connect = get_streamlit_authenticated_client(config.kite)
        
        if kite_connect:
            print("✅ Got authenticated KiteConnect client")
            
            # Test profile call
            profile = kite_connect.profile()
            print(f"✅ Profile call successful: {profile.get('user_id', 'Unknown')}")
            
            # Create KiteClient wrapper
            kite_client = KiteClient(
                api_key=config.kite.api_key,
                access_token=config.kite.access_token,
                api_secret=config.kite.api_secret
            )
            print("✅ KiteClient wrapper created successfully")
            
            # Test profile through wrapper
            wrapper_profile = kite_client.get_profile()
            print(f"✅ Wrapper profile call successful: {wrapper_profile.get('user_id', 'Unknown')}")
            
            return True
        else:
            print("❌ Could not get authenticated client")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Testing Caching Fix")
    print("=" * 25)
    
    success = test_client_creation()
    
    if success:
        print("\n🎉 All tests passed!")
        print("💡 The app should now work correctly without caching issues.")
    else:
        print("\n😞 Tests failed!")
        print("💡 There may still be configuration issues.")
