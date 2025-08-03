#!/usr/bin/env python3
"""
Kite Trading System Launcher

This script helps you start the trading system with proper configuration.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def check_virtual_environment():
    """Check if we're in a virtual environment."""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
        return True
    else:
        print("⚠️  Not in a virtual environment")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'streamlit',
        'kiteconnect', 
        'pandas',
        'numpy',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages


def check_env_file():
    """Check if .env file exists and has required variables."""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ .env file not found")
        print("Please create a .env file with your Kite API credentials:")
        print("KITE_API_KEY=your_api_key")
        print("KITE_ACCESS_TOKEN=your_access_token")
        return False
    
    print("✅ .env file found")
    
    # Check if required variables are present
    try:
        with open('.env', 'r') as f:
            content = f.read()
            
        if 'KITE_API_KEY=' in content and 'KITE_ACCESS_TOKEN=' in content:
            print("✅ Required environment variables found")
            return True
        else:
            print("⚠️  .env file exists but missing required variables")
            return False
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False


def run_tests():
    """Run tests to verify everything is working."""
    print("\n🧪 Running tests...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/test_config.py', '-v', '--tb=short'
        ], capture_output=True, text=True, cwd=Path.cwd())
        
        if result.returncode == 0:
            print("✅ Tests passed")
            return True
        else:
            print("❌ Tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def start_streamlit():
    """Start the Streamlit application."""
    print("\n🚀 Starting Kite Trading System...")
    
    try:
        # Set environment variable for Python path
        env = os.environ.copy()
        src_path = str(Path.cwd() / 'src')
        env['PYTHONPATH'] = src_path + os.pathsep + env.get('PYTHONPATH', '')
        
        print(f"Setting PYTHONPATH to: {src_path}")
        
        # Start Streamlit
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            'src/app.py',
            '--server.port=8501',
            '--server.headless=false'
        ], env=env, cwd=Path.cwd())
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error starting application: {e}")


def main():
    """Main launcher function."""
    print("🏢 Kite Trading System Launcher")
    print("=" * 40)
    
    # Check system requirements
    if not check_python_version():
        sys.exit(1)
    
    if not check_virtual_environment():
        print("Consider using a virtual environment for better isolation")
    
    # Check dependencies
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Check configuration
    if not check_env_file():
        print("\n📝 Please set up your .env file before continuing")
        sys.exit(1)
    
    # Run tests
    if '--skip-tests' not in sys.argv:
        if not run_tests():
            response = input("\n⚠️  Tests failed. Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
    
    # Start application
    start_streamlit()


if __name__ == "__main__":
    main()
