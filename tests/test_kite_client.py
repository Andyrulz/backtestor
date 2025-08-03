"""Tests for Kite client functionality."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date, timedelta
from src.kite.client import KiteClient
from src.kite.models import (
    OrderRequest,
    OrderType,
    TransactionType,
    ProductType,
    Exchange,
)


@pytest.fixture
def mock_kite_connect():
    """Mock KiteConnect instance."""
    with patch("src.kite.client.KiteConnect") as mock_class:
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        yield mock_class


@pytest.fixture
def kite_client(mock_kite_connect):
    """Create KiteClient instance with mocked KiteConnect."""
    return KiteClient(api_key="test_api_key", access_token="test_access_token")


class TestKiteClient:
    """Test cases for KiteClient."""
    
    def test_init(self, mock_kite_connect):
        """Test KiteClient initialization."""
        client = KiteClient(api_key="test_key", access_token="test_token")
        
        assert client.api_key == "test_key"
        assert client.access_token == "test_token"
        mock_kite_connect.assert_called_once_with(api_key="test_key")
        mock_kite_connect.return_value.set_access_token.assert_called_once_with("test_token")
    
    def test_place_order_success(self, kite_client, mock_kite_connect):
        """Test successful order placement."""
        # Mock response
        mock_kite_connect.return_value.place_order.return_value = {"order_id": "123456"}
        
        order_request = OrderRequest(
            tradingsymbol="RELIANCE",
            exchange=Exchange.NSE,
            transaction_type=TransactionType.BUY,
            order_type=OrderType.MARKET,
            quantity=1,
            product=ProductType.CNC,
        )
        
        order_id = kite_client.place_order(order_request)
        
        assert order_id == "123456"
        mock_kite_connect.return_value.place_order.assert_called_once()
    
    def test_place_order_with_price(self, kite_client, mock_kite_connect):
        """Test order placement with price."""
        mock_kite_connect.return_value.place_order.return_value = {"order_id": "123456"}
        
        order_request = OrderRequest(
            tradingsymbol="RELIANCE",
            exchange=Exchange.NSE,
            transaction_type=TransactionType.BUY,
            order_type=OrderType.LIMIT,
            quantity=1,
            product=ProductType.CNC,
            price=2500.0,
        )
        
        order_id = kite_client.place_order(order_request)
        
        assert order_id == "123456"
        
        # Verify price was included in the call
        call_args = mock_kite_connect.return_value.place_order.call_args[1]
        assert call_args["price"] == 2500.0
    
    def test_place_order_failure(self, kite_client, mock_kite_connect):
        """Test order placement failure."""
        mock_kite_connect.place_order.side_effect = Exception("API Error")
        
        order_request = OrderRequest(
            tradingsymbol="RELIANCE",
            exchange=Exchange.NSE,
            transaction_type=TransactionType.BUY,
            order_type=OrderType.MARKET,
            quantity=1,
            product=ProductType.CNC,
        )
        
        with pytest.raises(Exception, match="API Error"):
            kite_client.place_order(order_request)
    
    def test_get_orders_success(self, kite_client, mock_kite_connect):
        """Test successful orders retrieval."""
        mock_orders_data = [
            {
                "order_id": "123456",
                "order_timestamp": "2024-01-01 10:00:00",
                "exchange_order_id": "EX123",
                "tradingsymbol": "RELIANCE",
                "exchange": "NSE",
                "transaction_type": "BUY",
                "order_type": "MARKET",
                "product": "CNC",
                "quantity": 1,
                "price": 2500.0,
                "trigger_price": 0.0,
                "average_price": 2500.0,
                "pending_quantity": 0,
                "filled_quantity": 1,
                "cancelled_quantity": 0,
                "disclosed_quantity": 0,
                "validity": "DAY",
                "status": "COMPLETE",
                "status_message": None,
                "tag": None,
            }
        ]
        mock_kite_connect.orders.return_value = mock_orders_data
        
        orders = kite_client.get_orders()
        
        assert len(orders) == 1
        assert orders[0].order_id == "123456"
        assert orders[0].tradingsymbol == "RELIANCE"
        assert orders[0].status == "COMPLETE"
    
    def test_get_orders_empty(self, kite_client, mock_kite_connect):
        """Test orders retrieval with no orders."""
        mock_kite_connect.orders.return_value = []
        
        orders = kite_client.get_orders()
        
        assert len(orders) == 0
    
    def test_cancel_order_success(self, kite_client, mock_kite_connect):
        """Test successful order cancellation."""
        mock_kite_connect.cancel_order.return_value = {"order_id": "123456"}
        
        order_id = kite_client.cancel_order("123456")
        
        assert order_id == "123456"
        mock_kite_connect.cancel_order.assert_called_once_with(
            variety="regular", order_id="123456"
        )
    
    def test_get_historical_data_success(self, kite_client, mock_kite_connect):
        """Test successful historical data retrieval."""
        mock_data = [
            {
                "date": datetime(2024, 1, 1),
                "open": 2500.0,
                "high": 2550.0,
                "low": 2480.0,
                "close": 2520.0,
                "volume": 100000,
            }
        ]
        mock_kite_connect.historical_data.return_value = mock_data
        
        candles = kite_client.get_historical_data(
            instrument_token=738561,
            from_date=date(2024, 1, 1),
            to_date=date(2024, 1, 1),
            interval="day"
        )
        
        assert len(candles) == 1
        assert candles[0].open == 2500.0
        assert candles[0].close == 2520.0
    
    def test_get_margins_success(self, kite_client, mock_kite_connect):
        """Test successful margins retrieval."""
        mock_margins = {
            "equity": {
                "net": 100000.0,
                "available": {"cash": 50000.0},
                "utilised": {"debits": 50000.0},
            }
        }
        mock_kite_connect.margins.return_value = mock_margins
        
        margins = kite_client.get_margins()
        
        assert margins["equity"]["net"] == 100000.0
        assert margins["equity"]["available"]["cash"] == 50000.0
    
    def test_get_profile_success(self, kite_client, mock_kite_connect):
        """Test successful profile retrieval."""
        mock_profile = {
            "user_id": "TEST123",
            "user_name": "Test User",
            "email": "test@example.com",
            "broker": "ZERODHA",
            "exchanges": ["NSE", "BSE"],
            "products": ["CNC", "MIS"],
            "order_types": ["MARKET", "LIMIT"],
        }
        mock_kite_connect.profile.return_value = mock_profile
        
        profile = kite_client.get_profile()
        
        assert profile["user_id"] == "TEST123"
        assert profile["user_name"] == "Test User"
        assert "NSE" in profile["exchanges"]


class TestOrderRequest:
    """Test cases for OrderRequest model."""
    
    def test_order_request_creation(self):
        """Test OrderRequest creation with required fields."""
        order_request = OrderRequest(
            tradingsymbol="RELIANCE",
            exchange=Exchange.NSE,
            transaction_type=TransactionType.BUY,
            order_type=OrderType.MARKET,
            quantity=1,
            product=ProductType.CNC,
        )
        
        assert order_request.tradingsymbol == "RELIANCE"
        assert order_request.exchange == Exchange.NSE
        assert order_request.transaction_type == TransactionType.BUY
        assert order_request.order_type == OrderType.MARKET
        assert order_request.quantity == 1
        assert order_request.product == ProductType.CNC
        assert order_request.price is None
        assert order_request.trigger_price is None
    
    def test_order_request_with_optional_fields(self):
        """Test OrderRequest creation with optional fields."""
        order_request = OrderRequest(
            tradingsymbol="RELIANCE",
            exchange=Exchange.NSE,
            transaction_type=TransactionType.BUY,
            order_type=OrderType.LIMIT,
            quantity=1,
            product=ProductType.CNC,
            price=2500.0,
            trigger_price=2480.0,
            tag="test_order",
        )
        
        assert order_request.price == 2500.0
        assert order_request.trigger_price == 2480.0
        assert order_request.tag == "test_order"
