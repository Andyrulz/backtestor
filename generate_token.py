#!/usr/bin/env python3
"""Helper script to generate Kite access token."""

import sys
import os
from pathlib import Path
import webbrowser
from urllib.parse import urlparse, parse_qs

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from dotenv import load_dotenv
from kiteconnect import KiteConnect

# Load environment variables
load_dotenv()

def generate_access_token():
    """Generate a new access token for Kite API."""
    
    print("🔑 Kite Access Token Generator")
    print("=" * 40)
    
    api_key = os.getenv("KITE_API_KEY")
    api_secret = input("Enter your API Secret (from Kite Connect app): ").strip()
    
    if not api_key:
        print("❌ KITE_API_KEY not found in .env file")
        return
    
    if not api_secret:
        print("❌ API Secret is required")
        return
    
    try:
        # Initialize KiteConnect
        kite = KiteConnect(api_key=api_key)
        
        # Generate login URL
        login_url = kite.login_url()
        print(f"\n🌐 Opening login URL in browser...")
        print(f"URL: {login_url}")
        
        # Open browser
        webbrowser.open(login_url)
        
        print("\n📋 Instructions:")
        print("1. Complete the login process in the opened browser")
        print("2. After login, you'll be redirected to a URL")
        print("3. Copy the COMPLETE redirect URL and paste it below")
        print("4. The URL will contain 'request_token' parameter")
        print()
        
        # Get redirect URL from user
        redirect_url = input("Paste the complete redirect URL here: ").strip()
        
        if not redirect_url:
            print("❌ Redirect URL is required")
            return
        
        # Extract request token
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)
        
        if 'request_token' not in query_params:
            print("❌ No request_token found in the URL")
            print("Make sure you copied the complete redirect URL")
            return
        
        request_token = query_params['request_token'][0]
        print(f"\n🎯 Request token extracted: {request_token[:20]}...")
        
        # Generate access token
        print("🔄 Generating access token...")
        data = kite.generate_session(request_token, api_secret=api_secret)
        
        access_token = data["access_token"]
        user_id = data["user_id"]
        
        print(f"\n✅ Success! Access token generated")
        print(f"User ID: {user_id}")
        print(f"Access Token: {access_token}")
        
        # Update .env file
        env_path = Path(".env")
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Replace or add access token
            if "KITE_ACCESS_TOKEN=" in env_content:
                lines = env_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith("KITE_ACCESS_TOKEN="):
                        lines[i] = f"KITE_ACCESS_TOKEN={access_token}"
                        break
                env_content = '\n'.join(lines)
            else:
                env_content += f"\nKITE_ACCESS_TOKEN={access_token}"
            
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            print(f"\n📝 Updated .env file with new access token")
            print("🚀 You can now run the trading app!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")

def quick_token_check():
    """Quick check if current token works."""
    print("\n🔍 Testing current token...")
    
    api_key = os.getenv("KITE_API_KEY")
    access_token = os.getenv("KITE_ACCESS_TOKEN")
    
    if not api_key or not access_token:
        print("❌ Missing API key or access token")
        return False
    
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        profile = kite.profile()
        print(f"✅ Current token works! User: {profile.get('user_name', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ Current token invalid: {str(e)}")
        return False

if __name__ == "__main__":
    print("Zerodha Kite Access Token Generator")
    print("=" * 50)
    
    # First check if current token works
    if quick_token_check():
        print("\n🎉 Your current access token is working!")
        print("No need to generate a new one.")
    else:
        print("\n🔄 Generating new access token...")
        generate_access_token()
