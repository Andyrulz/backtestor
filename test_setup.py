#!/usr/bin/env python3
"""Test script to validate configuration and authentication setup."""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing Configuration...")
    
    try:
        from config import AppConfig
        config = AppConfig.from_env()
        
        print(f"✅ Configuration loaded successfully")
        print(f"   API Key: {config.kite.api_key[:10]}***")
        print(f"   API Secret: {config.kite.api_secret[:10]}***")
        print(f"   Access Token: {'Set' if config.kite.access_token else 'Not set'}")
        
        return True, config
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False, None


def test_kite_client_import():
    """Test Kite client import."""
    print("\n📦 Testing Kite Client Import...")
    
    try:
        from kite.client import KiteClient
        from kite.models import OrderRequest, Exchange, TransactionType, OrderType, ProductType
        
        print("✅ Kite client imports successful")
        return True
    except Exception as e:
        print(f"❌ Kite client import failed: {e}")
        return False


def test_auth_module():
    """Test authentication module."""
    print("\n🔐 Testing Authentication Module...")
    
    try:
        from auto_auth import AutoKiteAuth, get_auto_authenticated_client
        
        print("✅ Authentication module imports successful")
        return True
    except Exception as e:
        print(f"❌ Authentication module import failed: {e}")
        return False


def test_kite_connection():
    """Test minimal Kite connection without authentication."""
    print("\n🌐 Testing Kite Connection (without auth)...")
    
    try:
        from kiteconnect import KiteConnect
        
        success, config = test_configuration()
        if not success:
            return False
        
        # Just test instantiation, not actual connection
        kite = KiteConnect(api_key=config.kite.api_key)
        print("✅ KiteConnect instantiation successful")
        
        # Test login URL generation (this doesn't require authentication)
        login_url = kite.login_url()
        print(f"✅ Login URL generated: {login_url[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Kite connection test failed: {e}")
        return False


def test_streamlit_import():
    """Test Streamlit import."""
    print("\n🖥️  Testing Streamlit Import...")
    
    try:
        import streamlit as st
        print("✅ Streamlit import successful")
        return True
    except Exception as e:
        print(f"❌ Streamlit import failed: {e}")
        return False


def main():
    """Main test function."""
    print("🧪 Testing Kite Trading System Setup")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_kite_client_import,
        test_auth_module,
        test_streamlit_import,
        test_kite_connection,
    ]
    
    results = []
    for test in tests:
        if callable(test):
            if test.__name__ == 'test_configuration':
                success, _ = test()
                results.append(success)
            else:
                results.append(test())
        else:
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    test_names = [
        "Configuration Loading",
        "Kite Client Import", 
        "Authentication Module",
        "Streamlit Import",
        "Kite Connection"
    ]
    
    passed = 0
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Summary: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! System is ready for authentication testing.")
        print("\n📝 Next Steps:")
        print("   1. Run 'python test_auth.py' to test the login flow")
        print("   2. Run 'streamlit run src/app.py' to start the web interface")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before proceeding.")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
