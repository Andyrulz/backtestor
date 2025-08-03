"""Integration tests for Kite API functionality with mocked responses."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from src.kite.client import KiteClient
from src.kite.models import OrderRequest, OrderType, TransactionType, ProductType, Exchange


class TestKiteAPIIntegration:
    """Integration tests for Kite API with mocked responses."""

    @pytest.fixture
    def mock_successful_kite_response(self):
        """Mock successful Kite API responses."""
        mock_response = {
            "orders": [
                {
                    "order_id": "TEST123",
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
            ],
            "margins": {
                "equity": {
                    "net": 100000.0,
                    "available": {"cash": 50000.0},
                    "utilised": {"debits": 50000.0},
                }
            },
            "profile": {
                "user_id": "TEST123",
                "user_name": "Test User",
                "email": "test@example.com",
                "broker": "ZERODHA",
                "exchanges": ["NSE", "BSE"],
                "products": ["CNC", "MIS"],
                "order_types": ["MARKET", "LIMIT"],
            },
            "historical_data": [
                {
                    "date": datetime(2024, 1, 1),
                    "open": 2500.0,
                    "high": 2550.0,
                    "low": 2480.0,
                    "close": 2520.0,
                    "volume": 100000,
                }
            ]
        }
        return mock_response

    @patch('src.kite.client.KiteConnect')
    def test_successful_order_placement_integration(self, mock_kite_connect, mock_successful_kite_response):
        """Test successful order placement with mocked API."""
        # Setup mock
        mock_instance = Mock()
        mock_kite_connect.return_value = mock_instance
        mock_instance.place_order.return_value = {"order_id": "TEST123"}
        
        # Create client
        client = KiteClient("test_key", "test_token")
        
        # Create order request
        order_request = OrderRequest(
            tradingsymbol="RELIANCE",
            exchange=Exchange.NSE,
            transaction_type=TransactionType.BUY,
            order_type=OrderType.MARKET,
            quantity=1,
            product=ProductType.CNC,
        )
        
        # Place order
        order_id = client.place_order(order_request)
        
        # Verify
        assert order_id == "TEST123"
        mock_instance.place_order.assert_called_once()

    @patch('src.kite.client.KiteConnect')
    def test_order_retrieval_integration(self, mock_kite_connect, mock_successful_kite_response):
        """Test order retrieval with mocked API."""
        # Setup mock
        mock_instance = Mock()
        mock_kite_connect.return_value = mock_instance
        mock_instance.orders.return_value = mock_successful_kite_response["orders"]
        
        # Create client and get orders
        client = KiteClient("test_key", "test_token")
        orders = client.get_orders()
        
        # Verify
        assert len(orders) == 1
        assert orders[0].order_id == "TEST123"
        assert orders[0].tradingsymbol == "RELIANCE"

    @patch('src.kite.client.KiteConnect')
    def test_margins_retrieval_integration(self, mock_kite_connect, mock_successful_kite_response):
        """Test margins retrieval with mocked API."""
        # Setup mock
        mock_instance = Mock()
        mock_kite_connect.return_value = mock_instance
        mock_instance.margins.return_value = mock_successful_kite_response["margins"]
        
        # Create client and get margins
        client = KiteClient("test_key", "test_token")
        margins = client.get_margins()
        
        # Verify
        assert margins["equity"]["net"] == 100000.0
        assert margins["equity"]["available"]["cash"] == 50000.0

    @patch('src.kite.client.KiteConnect')
    def test_profile_retrieval_integration(self, mock_kite_connect, mock_successful_kite_response):
        """Test profile retrieval with mocked API."""
        # Setup mock
        mock_instance = Mock()
        mock_kite_connect.return_value = mock_instance
        mock_instance.profile.return_value = mock_successful_kite_response["profile"]
        
        # Create client and get profile
        client = KiteClient("test_key", "test_token")
        profile = client.get_profile()
        
        # Verify
        assert profile["user_id"] == "TEST123"
        assert profile["user_name"] == "Test User"
        assert "NSE" in profile["exchanges"]

    @patch('src.kite.client.KiteConnect')
    def test_historical_data_integration(self, mock_kite_connect, mock_successful_kite_response):
        """Test historical data retrieval with mocked API."""
        # Setup mock
        mock_instance = Mock()
        mock_kite_connect.return_value = mock_instance
        mock_instance.historical_data.return_value = mock_successful_kite_response["historical_data"]
        
        # Create client and get data
        client = KiteClient("test_key", "test_token")
        candles = client.get_historical_data(
            instrument_token=738561,
            from_date=date(2024, 1, 1),
            to_date=date(2024, 1, 1)
        )
        
        # Verify
        assert len(candles) == 1
        assert candles[0].open == 2500.0
        assert candles[0].close == 2520.0

    @patch('src.kite.client.KiteConnect')
    def test_api_error_handling_integration(self, mock_kite_connect):
        """Test API error handling in integration scenarios."""
        # Setup mock to raise exception
        mock_instance = Mock()
        mock_kite_connect.return_value = mock_instance
        mock_instance.orders.side_effect = Exception("API Error")
        
        # Create client
        client = KiteClient("test_key", "test_token")
        
        # Test error handling
        with pytest.raises(Exception, match="API Error"):
            client.get_orders()

    @patch('src.kite.client.KiteConnect')
    def test_rate_limiting_simulation(self, mock_kite_connect):
        """Test behavior under rate limiting conditions."""
        # Setup mock to simulate rate limiting
        mock_instance = Mock()
        mock_kite_connect.return_value = mock_instance
        mock_instance.orders.side_effect = Exception("Too many requests")
        
        # Create client
        client = KiteClient("test_key", "test_token")
        
        # Test rate limiting handling
        with pytest.raises(Exception, match="Too many requests"):
            client.get_orders()


class TestDataValidationIntegration:
    """Integration tests for data validation and processing."""

    @patch('src.kite.client.KiteConnect')
    def test_order_data_validation(self, mock_kite_connect):
        """Test order data validation in integration context."""
        # Setup mock with invalid data
        mock_instance = Mock()
        mock_kite_connect.return_value = mock_instance
        
        invalid_order_data = [
            {
                "order_id": "TEST123",
                "order_timestamp": "invalid-date",  # Invalid date format
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
            }
        ]
        
        mock_instance.orders.return_value = invalid_order_data
        
        # Create client
        client = KiteClient("test_key", "test_token")
        
        # Should handle invalid data gracefully
        with pytest.raises(ValueError):
            client.get_orders()

    @patch('src.kite.client.KiteConnect')
    def test_empty_response_handling(self, mock_kite_connect):
        """Test handling of empty API responses."""
        # Setup mock with empty response
        mock_instance = Mock()
        mock_kite_connect.return_value = mock_instance
        mock_instance.orders.return_value = []
        
        # Create client
        client = KiteClient("test_key", "test_token")
        
        # Should handle empty response
        orders = client.get_orders()
        assert len(orders) == 0

    @patch('src.kite.client.KiteConnect')
    def test_partial_data_handling(self, mock_kite_connect):
        """Test handling of partial/incomplete data."""
        # Setup mock with partial data
        mock_instance = Mock()
        mock_kite_connect.return_value = mock_instance
        
        partial_order_data = [
            {
                "order_id": "TEST123",
                "order_timestamp": "2024-01-01 10:00:00",
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
                # Missing optional fields like status_message, tag, etc.
            }
        ]
        
        mock_instance.orders.return_value = partial_order_data
        
        # Create client
        client = KiteClient("test_key", "test_token")
        
        # Should handle partial data
        orders = client.get_orders()
        assert len(orders) == 1
        assert orders[0].status_message is None
        assert orders[0].tag is None
