#!/usr/bin/env python3
"""Test orders retrieval."""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from config import AppConfig
from kite.client import KiteClient

def test_orders():
    """Test getting orders."""
    try:
        # Load configuration
        config = AppConfig.from_env()
        
        # Create client
        client = KiteClient(
            api_key=config.kite.api_key,
            access_token=config.kite.access_token,
            api_secret=config.kite.api_secret
        )
        
        print("Testing orders retrieval...")
        
        # Get orders
        orders = client.get_orders()
        print(f"✅ Retrieved {len(orders)} orders successfully!")
        
        if orders:
            print("\nRecent orders:")
            for i, order in enumerate(orders[:3]):  # Show first 3 orders
                print(f"  {i+1}. {order.tradingsymbol} - {order.transaction_type} {order.quantity} @ {order.price} - {order.status}")
        else:
            print("  No orders found for today")
        
    except Exception as e:
        print(f"❌ Orders retrieval failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_orders()
