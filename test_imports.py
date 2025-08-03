#!/usr/bin/env python3
"""Test script to verify imports work correctly."""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

print(f"Python path: {sys.path[:3]}")
print(f"Current directory: {os.getcwd()}")
print(f"Src directory: {src_dir}")

try:
    print("Testing config import...")
    from config import AppConfig
    print("✅ config imported successfully")
except Exception as e:
    print(f"❌ config import failed: {e}")

try:
    print("Testing kite.models import...")
    from kite.models import OrderType
    print("✅ kite.models imported successfully")
except Exception as e:
    print(f"❌ kite.models import failed: {e}")

try:
    print("Testing kite.client import...")
    from kite.client import KiteClient
    print("✅ kite.client imported successfully")
except Exception as e:
    print(f"❌ kite.client import failed: {e}")

try:
    print("Testing ui.components import...")
    from ui.components import render_order_form
    print("✅ ui.components imported successfully")
except Exception as e:
    print(f"❌ ui.components import failed: {e}")

print("\n🎉 All imports successful! The app should work now.")
