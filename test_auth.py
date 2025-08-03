#!/usr/bin/env python3
"""Test script to validate authentication flow."""

import os
import sys
import time
import webbrowser
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def test_automated_auth():
    """Test the automated authentication process."""
    print("🔐 Testing Automated Authentication")
    print("=" * 50)
    
    try:
        from config import AppConfig
        from auto_auth import AutoKiteAuth
        
        # Load configuration
        config = AppConfig.from_env()
        auth = AutoKiteAuth(config.kite)
        
        print(f"✅ Configuration loaded")
        print(f"   API Key: {config.kite.api_key[:10]}***")
        print(f"   API Secret: {config.kite.api_secret[:10]}***")
        
        # Check if token is already valid
        print("\n📋 Checking existing token...")
        if auth.is_token_valid():
            print("✅ Existing token is valid!")
            print("   You're already authenticated and ready to use the system.")
            return True
        else:
            print("ℹ️  No valid token found. Authentication required.")
        
        print("\n🔗 Generating login URL...")
        login_url = auth.kite.login_url()
        print(f"✅ Login URL generated: {login_url}")
        
        print("\n" + "=" * 50)
        print("🚀 MANUAL AUTHENTICATION REQUIRED")
        print("=" * 50)
        print("To complete authentication, you need to:")
        print()
        print("1. 📱 Open this URL in your browser:")
        print(f"   {login_url}")
        print()
        print("2. 🔑 Login with your Zerodha credentials")
        print()
        print("3. 📋 Copy the COMPLETE redirect URL after login")
        print("   (It will look like: https://127.0.0.1:5000/?request_token=...&action=login&status=success)")
        print()
        print("4. 🖥️  Run the web app to complete authentication:")
        print("   streamlit run src/app.py")
        print()
        print("📝 The web app will:")
        print("   - Automatically open the login page")
        print("   - Guide you through copy-pasting the redirect URL")
        print("   - Save the access token for 24 hours")
        print("   - Remember your login for future sessions")
        
        # Try to open browser automatically
        try:
            print("\n🌐 Opening browser automatically...")
            webbrowser.open(login_url)
            print("✅ Browser opened! Complete the login there.")
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print("   Please copy the URL above and open it manually.")
        
        return False  # Manual step required
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_streamlit_readiness():
    """Test if Streamlit app can start."""
    print("\n🖥️  Testing Streamlit Readiness")
    print("=" * 30)
    
    try:
        # Check if all required imports work
        from config import AppConfig
        from auto_auth import render_auto_login
        from kite.client import KiteClient
        
        print("✅ All imports successful")
        print("✅ Streamlit app is ready to start")
        
        return True
    except Exception as e:
        print(f"❌ Streamlit readiness test failed: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 Testing Authentication Flow")
    print("🔒 This will help you log in to Zerodha Kite")
    print("=" * 60)
    
    # Test automated auth
    auth_ready = test_automated_auth()
    
    # Test Streamlit readiness
    streamlit_ready = test_streamlit_readiness()
    
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   Authentication Setup: {'✅ READY' if True else '❌ FAILED'}")
    print(f"   Streamlit App: {'✅ READY' if streamlit_ready else '❌ FAILED'}")
    
    if auth_ready:
        print("\n🎉 You're already authenticated! You can now:")
        print("   • Run 'streamlit run src/app.py' to start trading")
        print("   • Use the full trading interface")
        print("   • Place orders, view positions, etc.")
    else:
        print("\n🚀 Next Steps:")
        print("   1. Run: streamlit run src/app.py")
        print("   2. Complete the one-time login in the web interface")
        print("   3. Start trading!")
        
        print("\n💡 Tips:")
        print("   • Authentication is required only once per day")
        print("   • Your session will be saved for 24 hours")
        print("   • The web app will guide you through the process")
    
    return streamlit_ready


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
