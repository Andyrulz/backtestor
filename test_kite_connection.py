#!/usr/bin/env python3
"""Test script to debug Kite API connection issues."""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from dotenv import load_dotenv
from kiteconnect import KiteConnect

# Load environment variables
load_dotenv()

def test_kite_connection():
    """Test Kite API connection with detailed debugging."""
    
    print("🔍 Testing Kite API Connection...")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv("KITE_API_KEY")
    access_token = os.getenv("KITE_ACCESS_TOKEN")
    
    print(f"API Key: {api_key[:10] + '...' if api_key else 'NOT FOUND'}")
    print(f"Access Token: {access_token[:10] + '...' if access_token else 'NOT FOUND'}")
    print()
    
    if not api_key:
        print("❌ KITE_API_KEY not found in environment variables")
        return False
        
    if not access_token:
        print("❌ KITE_ACCESS_TOKEN not found in environment variables")
        return False
    
    try:
        # Initialize KiteConnect directly
        print("🔌 Initializing KiteConnect...")
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Test basic API call
        print("📋 Testing profile API call...")
        profile = kite.profile()
        
        print("✅ Connection successful!")
        print(f"User ID: {profile.get('user_id', 'N/A')}")
        print(f"User Name: {profile.get('user_name', 'N/A')}")
        print(f"Email: {profile.get('email', 'N/A')}")
        print(f"Broker: {profile.get('broker', 'N/A')}")
        
        # Test additional API calls
        print("\n📊 Testing additional API calls...")
        
        try:
            margins = kite.margins()
            print("✅ Margins API: Success")
        except Exception as e:
            print(f"❌ Margins API: {str(e)}")
        
        try:
            orders = kite.orders()
            print(f"✅ Orders API: Success ({len(orders)} orders)")
        except Exception as e:
            print(f"❌ Orders API: {str(e)}")
            
        try:
            positions = kite.positions()
            print(f"✅ Positions API: Success")
        except Exception as e:
            print(f"❌ Positions API: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # Provide specific guidance based on error type
        error_msg = str(e).lower()
        if "incorrect api_key" in error_msg or "access_token" in error_msg:
            print("\n💡 Troubleshooting suggestions:")
            print("1. Verify your API key and access token are correct")
            print("2. Make sure the access token is not expired")
            print("3. Check if your Kite Connect app is active")
            print("4. Ensure you're using the correct API credentials")
            print("\n📖 How to get correct credentials:")
            print("1. Login to https://kite.trade/")
            print("2. Go to 'Apps' section")
            print("3. Create or select your app")
            print("4. Copy the API Key")
            print("5. Generate a new access token using the request token flow")
            
        elif "network" in error_msg or "connection" in error_msg:
            print("\n💡 Network issue detected:")
            print("1. Check your internet connection")
            print("2. Verify firewall settings")
            print("3. Try again in a few minutes")
            
        return False

if __name__ == "__main__":
    test_kite_connection()
