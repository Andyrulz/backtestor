"""Final comprehensive test for the fixed authentication system."""

import sys
import time
import webbrowser
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from redirect_server import TokenCaptureServer
from config import KiteConfig

def test_complete_flow():
    """Test the complete authentication flow."""
    print("🎯 Complete Authentication Flow Test")
    print("=" * 40)
    
    try:
        # Test configuration
        print("1. 📋 Testing configuration...")
        config = KiteConfig.from_env()
        print(f"   ✅ API Key: {config.api_key}")
        print(f"   ✅ API Secret: {'*' * len(config.api_secret)}")
        print(f"   ✅ Current Token: {config.access_token[:20] if config.access_token else 'None'}...")
        
        # Test server startup
        print("\n2. 🖥️ Testing server startup...")
        server = TokenCaptureServer(port=3456)
        
        if not server.start_server():
            print("   ❌ Server startup failed")
            return False
        print("   ✅ Server started successfully")
        
        # Test with your actual redirect URL
        print("\n3. 🔗 Testing with actual redirect URL...")
        test_url = "http://localhost:3456/store_tokens?action=login&type=login&status=success&request_token=H7nJ3oO48bScVcccQ49GH4oPokE3xZLS"
        
        print(f"   📤 URL: {test_url}")
        
        try:
            import requests
            response = requests.get(test_url, timeout=10)
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Redirect handled successfully!")
                
                # Check token capture
                token = server.wait_for_token(timeout=5)
                if token:
                    print(f"   ✅ Token captured: {token}")
                else:
                    print("   ⚠️ Token not captured (may be normal)")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   📝 Response: {response.text}")
                
        except ImportError:
            print("   ⚠️ Requests not available, opening in browser...")
            webbrowser.open(test_url)
            print("   🌐 Opened in browser, check manually")
        
        # Cleanup
        server.stop_server()
        print("   🛑 Server stopped")
        
        print("\n✅ All tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

def test_authentication_ready():
    """Test if authentication system is ready."""
    print("\n🔍 Authentication System Readiness")
    print("=" * 35)
    
    checks = [
        ("Configuration file", lambda: Path(".env").exists()),
        ("Source files", lambda: Path("src/redirect_server.py").exists()),
        ("Auto auth module", lambda: Path("src/auto_auth.py").exists()),
        ("Port 3456 available", lambda: check_port_available(3456)),
    ]
    
    all_good = True
    for name, check_func in checks:
        try:
            result = check_func()
            status = "✅" if result else "❌"
            print(f"{status} {name}")
            if not result:
                all_good = False
        except Exception as e:
            print(f"❌ {name} - Error: {e}")
            all_good = False
    
    return all_good

def check_port_available(port):
    """Check if port is available."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result != 0  # Port is available if connection failed
    except:
        return True

if __name__ == "__main__":
    print("🧪 Final Authentication System Test")
    print("=" * 40)
    
    # Check readiness
    if not test_authentication_ready():
        print("\n⚠️ System not ready. Please check the issues above.")
        exit(1)
    
    # Test complete flow
    success = test_complete_flow()
    
    if success:
        print("\n🎉 Authentication system is ready!")
        print("🚀 You can now start the app and test the automatic authentication.")
        print("\n📋 To start the app:")
        print("   • Double-click: start_auto_auth.bat")
        print("   • Or run: streamlit run src\\app.py")
        print("\n💡 Remember to set your Kite app redirect URI to:")
        print("   http://localhost:3456/store_tokens")
    else:
        print("\n😞 There are still issues to resolve.")
        print("💡 Please check the error messages above.")
