"""Test script for the automatic token capture system."""

import time
import webbrowser
from src.redirect_server import TokenCaptureServer

def test_automatic_capture():
    """Test the automatic token capture functionality."""
    print("🚀 Testing Automatic Token Capture System")
    print("=" * 50)
    
    # Start the redirect server
    print("1. Starting redirect server on port 3456...")
    server = TokenCaptureServer(port=3456)
    
    if not server.start_server():
        print("❌ Failed to start server")
        return False
    
    print("✅ Server started successfully!")
    print(f"🌐 Server running at: http://localhost:3456")
    
    # Simulate the login redirect
    print("\n2. Simulating Kite login redirect...")
    test_url = "http://localhost:3456/store_tokens?action=login&type=login&status=success&request_token=test_token_ABC123DEF456"
    
    print(f"📤 Opening test URL: {test_url}")
    time.sleep(1)
    
    try:
        webbrowser.open(test_url)
        print("✅ Test URL opened in browser")
    except Exception as e:
        print(f"⚠️ Could not auto-open browser: {e}")
        print(f"Please manually open: {test_url}")
    
    # Wait for token capture
    print("\n3. Waiting for token capture...")
    print("⏳ Waiting up to 30 seconds...")
    
    token = server.wait_for_token(timeout=30)
    
    if token:
        print(f"✅ Token captured successfully: {token}")
        print(f"🎯 Full token: {token}")
        
        # Stop server
        server.stop_server()
        print("🛑 Server stopped")
        
        print("\n✅ Test completed successfully!")
        return True
    else:
        print("❌ No token captured within timeout")
        server.stop_server()
        print("🛑 Server stopped")
        
        print("\n❌ Test failed!")
        return False

def test_server_availability():
    """Test if port 3456 is available."""
    import socket
    
    print("🔍 Checking port 3456 availability...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 3456))
        sock.close()
        
        if result == 0:
            print("⚠️ Port 3456 is already in use")
            return False
        else:
            print("✅ Port 3456 is available")
            return True
    except Exception as e:
        print(f"❌ Error checking port: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Kite Token Capture Test Suite")
    print("=" * 40)
    
    # Test port availability
    if not test_server_availability():
        print("\n💡 If port 3456 is in use, the app might already be running")
        print("   or another process is using this port.")
        exit(1)
    
    print()
    
    # Test automatic capture
    success = test_automatic_capture()
    
    if success:
        print("\n🎉 All tests passed!")
        print("💡 The automatic token capture system is working correctly.")
        print("   You can now use the app with automatic authentication.")
    else:
        print("\n😞 Tests failed!")
        print("💡 Please check the error messages above.")
        print("   You may need to use the manual backup method.")
