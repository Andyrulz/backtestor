#!/usr/bin/env python3
"""Setup script for the trading strategies system."""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Main setup function."""
    print("🚀 Setting up Kite Trading System with Strategies")
    print("=" * 50)
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    if not (current_dir / "src" / "app.py").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print("✅ Python version check passed")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e.stderr}")
        sys.exit(1)
    
    # Check environment file
    env_file = current_dir / ".env"
    if not env_file.exists():
        print("❌ .env file not found. Please create it with your Kite API credentials")
        sys.exit(1)
    
    print("✅ Environment file found")
    
    # Check API credentials
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    if "KITE_API_KEY=" not in env_content or "KITE_API_SECRET=" not in env_content:
        print("❌ Missing API credentials in .env file")
        print("Please ensure you have:")
        print("  KITE_API_KEY=your_api_key")
        print("  KITE_API_SECRET=your_api_secret")
        sys.exit(1)
    
    print("✅ API credentials configured")
    
    # Test import of strategies
    try:
        sys.path.insert(0, str(current_dir / "src"))
        from strategies import StrategyManager, MovingAverageCrossover
        print("✅ Strategy framework loaded successfully")
    except ImportError as e:
        print(f"❌ Failed to import strategies: {e}")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n🚀 Next steps:")
    print("1. Run the application: python launch.py")
    print("2. Complete the one-time Zerodha login")
    print("3. Navigate to the 'Strategies' tab to set up your first strategy")
    print("4. Use 'Strategy Config' tab to create and manage strategies")
    
    print("\n💡 Available strategy types:")
    print("• Moving Average Crossover")
    print("• RSI Mean Reversion")
    print("• Bollinger Bands")
    print("• MACD Momentum")
    
    print("\n⚠️  Important:")
    print("• Start with 'dry run' mode to test strategies")
    print("• Enable 'Auto Execute' only after thorough testing")
    print("• Use proper risk management settings")


if __name__ == "__main__":
    main()
