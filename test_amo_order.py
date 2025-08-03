#!/usr/bin/env python3
"""Test AMO order placement."""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from config import AppConfig
from kite.client import KiteClient
from kite.models import OrderRequest, OrderVariety, Exchange, TransactionType, OrderType, ProductType

def test_amo_order():
    """Test placing an AMO order."""
    try:
        # Load configuration
        config = AppConfig.from_env()
        
        # Create client
        client = KiteClient(
            api_key=config.kite.api_key,
            access_token=config.kite.access_token,
            api_secret=config.kite.api_secret
        )
        
        print("Testing AMO order placement...")
        
        # Create a simple AMO order with realistic price
        order_request = OrderRequest(
            variety=OrderVariety.AMO,
            tradingsymbol="RELIANCE",
            exchange=Exchange.NSE,
            transaction_type=TransactionType.BUY,
            order_type=OrderType.LIMIT,
            quantity=1,
            product=ProductType.CNC,
            price=1530.0,  # Within circuit limit
            validity="DAY"
        )
        
        print(f"Order request: {order_request}")
        
        # Place order
        order_id = client.place_order(order_request)
        print(f"✅ AMO Order placed successfully! Order ID: {order_id}")
        
    except Exception as e:
        print(f"❌ AMO Order placement failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_amo_order()
