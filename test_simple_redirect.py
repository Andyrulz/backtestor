"""Simple test for redirect server functionality."""

import requests
import time
from src.redirect_server import TokenCaptureServer

def test_redirect_endpoint():
    """Test the redirect endpoint directly."""
    print("🧪 Testing Redirect Server Fix")
    print("=" * 35)
    
    # Start server
    server = TokenCaptureServer(port=3456)
    
    if not server.start_server():
        print("❌ Failed to start server")
        return False
    
    print("✅ Server started successfully")
    
    # Give server time to start
    time.sleep(1)
    
    try:
        # Test the endpoint with your actual token
        test_url = "http://localhost:3456/store_tokens?action=login&type=login&status=success&request_token=H7nJ3oO48bScVcccQ49GH4oPokE3xZLS"
        
        print(f"🌐 Testing URL: {test_url}")
        
        response = requests.get(test_url, timeout=5)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Server responded successfully!")
            print("🎯 Token should be captured...")
            
            # Check if token was captured
            token = server.wait_for_token(timeout=5)
            if token:
                print(f"✅ Token captured: {token}")
                result = True
            else:
                print("❌ Token not captured")
                result = False
        else:
            print(f"❌ Server error: {response.status_code}")
            print(f"📝 Response content: {response.text}")
            result = False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        result = False
    
    finally:
        server.stop_server()
        print("🛑 Server stopped")
    
    return result

if __name__ == "__main__":
    success = test_redirect_endpoint()
    if success:
        print("\n🎉 Redirect server is working correctly!")
        print("💡 You can now try the authentication flow again.")
    else:
        print("\n😞 There's still an issue with the redirect server.")
        print("💡 Please check the error messages above.")
