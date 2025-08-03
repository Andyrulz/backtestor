#!/usr/bin/env python3
"""Test the authentication system without Streamlit dependencies."""

import sys
import os
import time
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from config import AppConfig
from kiteconnect import KiteConnect

def test_current_token():
    """Test if current token in .env works."""
    
    print("🔍 Testing Current Access Token...")
    print("=" * 50)
    
    try:
        # Load configuration
        config = AppConfig.from_env()
        print(f"✅ Configuration loaded")
        print(f"   API Key: {config.kite.api_key[:10]}...")
        print(f"   API Secret: {config.kite.api_secret[:10]}...")
        print(f"   Access Token: {config.kite.access_token[:10]}..." if config.kite.access_token else "   Access Token: Not set")
        print()
        
        if not config.kite.access_token:
            print("❌ No access token found in .env file")
            return False
        
        # Test token
        print("🔐 Testing token with Kite API...")
        kite = KiteConnect(api_key=config.kite.api_key)
        kite.set_access_token(config.kite.access_token)
        
        profile = kite.profile()
        
        print("✅ Token is valid!")
        print(f"👤 User: {profile.get('user_name', 'Unknown')}")
        print(f"📧 Email: {profile.get('email', 'N/A')}")
        print(f"🆔 User ID: {profile.get('user_id', 'N/A')}")
        print(f"🏦 Broker: {profile.get('broker', 'N/A')}")
        print()
        
        # Test additional APIs
        print("📊 Testing additional APIs...")
        
        try:
            margins = kite.margins()
            print(f"✅ Margins API: Working")
        except Exception as e:
            print(f"❌ Margins API: {str(e)}")
        
        try:
            orders = kite.orders()
            print(f"✅ Orders API: Working ({len(orders)} orders today)")
        except Exception as e:
            print(f"❌ Orders API: {str(e)}")
        
        try:
            positions = kite.positions()
            net_positions = positions.get('net', [])
            day_positions = positions.get('day', [])
            print(f"✅ Positions API: Working ({len(net_positions)} net, {len(day_positions)} day)")
        except Exception as e:
            print(f"❌ Positions API: {str(e)}")
        
        print()
        print("🎉 Your token is working! You can run the trading app now.")
        print("💡 Run: streamlit run src\\app.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Token test failed: {str(e)}")
        print()
        print("💡 Solutions:")
        print("1. The access token might be expired (tokens expire daily)")
        print("2. Run the app to get a new token: streamlit run src\\app.py")
        print("3. Complete the one-time login process")
        print("4. The new token will be saved automatically")
        
        return False

def check_token_expiry():
    """Check if we have session info."""
    
    print("\n🕐 Checking Token Session Info...")
    print("-" * 30)
    
    token_file = Path(__file__).parent / ".kite_session"
    
    if token_file.exists():
        try:
            with open(token_file, 'r') as f:
                token_data = f.read().strip().split('|')
                if len(token_data) >= 2:
                    timestamp = float(token_data[1])
                    hours_ago = (time.time() - timestamp) / 3600
                    hours_left = 24 - hours_ago
                    
                    if hours_left > 0:
                        print(f"⏰ Token created {hours_ago:.1f} hours ago")
                        print(f"⌛ Expires in {hours_left:.1f} hours")
                    else:
                        print(f"⏰ Token expired {abs(hours_left):.1f} hours ago")
                        print("🔄 New login required")
        except Exception as e:
            print(f"❌ Error reading session file: {e}")
    else:
        print("📄 No session file found")
        print("💡 Token will be saved after first successful login")

if __name__ == "__main__":
    print("Kite Trading System - Token Verification")
    print("=" * 60)
    
    success = test_current_token()
    check_token_expiry()
    
    print("\n" + "=" * 60)
    if success:
        print("🟢 READY: Your trading system is ready to use!")
    else:
        print("🟡 SETUP NEEDED: Run the app to complete authentication")
    
    print("\n🚀 Next Steps:")
    print("1. Run: streamlit run src\\app.py")
    print("2. Your browser will open automatically")
    if not success:
        print("3. Complete the one-time login (copy-paste URL)")
        print("4. Token will be saved for 24 hours")
    else:
        print("3. Start trading!")
