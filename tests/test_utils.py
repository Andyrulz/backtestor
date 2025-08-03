"""Test utilities and helpers for the trading system tests."""

import os
import tempfile
from contextlib import contextmanager
from typing import Dict, Any, Generator
from unittest.mock import Mock, patch
from src.kite.models import Order, Candle, Position, Instrument
from datetime import datetime, date


class TestDataFactory:
    """Factory for creating test data objects."""
    
    @staticmethod
    def create_test_order(
        order_id: str = "TEST123",
        tradingsymbol: str = "RELIANCE",
        status: str = "COMPLETE",
        **kwargs
    ) -> Order:
        """Create a test Order object with default values."""
        defaults = {
            "order_id": order_id,
            "order_timestamp": datetime(2024, 1, 1, 10, 0, 0),
            "exchange_order_id": "EX123",
            "tradingsymbol": tradingsymbol,
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
            "status": status,
            "status_message": None,
            "tag": None,
        }
        defaults.update(kwargs)
        return Order(**defaults)
    
    @staticmethod
    def create_test_candle(
        date_val: datetime = None,
        open_price: float = 2500.0,
        **kwargs
    ) -> Candle:
        """Create a test Candle object with default values."""
        if date_val is None:
            date_val = datetime(2024, 1, 1)
        
        defaults = {
            "date": date_val,
            "open": open_price,
            "high": open_price + 50.0,
            "low": open_price - 20.0,
            "close": open_price + 20.0,
            "volume": 100000,
        }
        defaults.update(kwargs)
        return Candle(**defaults)
    
    @staticmethod
    def create_test_position(
        tradingsymbol: str = "RELIANCE",
        quantity: int = 10,
        **kwargs
    ) -> Position:
        """Create a test Position object with default values."""
        defaults = {
            "tradingsymbol": tradingsymbol,
            "exchange": "NSE",
            "instrument_token": 738561,
            "product": "CNC",
            "quantity": quantity,
            "overnight_quantity": 0,
            "multiplier": 1,
            "average_price": 2500.0,
            "close_price": 2520.0,
            "last_price": 2510.0,
            "value": quantity * 2500.0,
            "pnl": quantity * 10.0,
            "m2m": quantity * 10.0,
            "unrealised": quantity * 10.0,
            "realised": 0.0,
        }
        defaults.update(kwargs)
        return Position(**defaults)
    
    @staticmethod
    def create_test_instrument(
        tradingsymbol: str = "RELIANCE",
        instrument_token: int = 738561,
        **kwargs
    ) -> Instrument:
        """Create a test Instrument object with default values."""
        defaults = {
            "instrument_token": instrument_token,
            "exchange_token": 738561,
            "tradingsymbol": tradingsymbol,
            "name": "RELIANCE INDUSTRIES LTD",
            "last_price": 2500.0,
            "expiry": None,
            "strike": None,
            "tick_size": 0.05,
            "lot_size": 1,
            "instrument_type": "EQ",
            "segment": "NSE",
            "exchange": "NSE",
        }
        defaults.update(kwargs)
        return Instrument(**defaults)


class MockKiteClientBuilder:
    """Builder for creating mock KiteClient instances with predefined responses."""
    
    def __init__(self):
        self.mock_responses = {}
        self.mock_exceptions = {}
    
    def with_orders(self, orders: list) -> 'MockKiteClientBuilder':
        """Add mock orders response."""
        self.mock_responses['orders'] = orders
        return self
    
    def with_positions(self, positions: list) -> 'MockKiteClientBuilder':
        """Add mock positions response."""
        self.mock_responses['positions'] = positions
        return self
    
    def with_margins(self, margins: dict) -> 'MockKiteClientBuilder':
        """Add mock margins response."""
        self.mock_responses['margins'] = margins
        return self
    
    def with_profile(self, profile: dict) -> 'MockKiteClientBuilder':
        """Add mock profile response."""
        self.mock_responses['profile'] = profile
        return self
    
    def with_historical_data(self, candles: list) -> 'MockKiteClientBuilder':
        """Add mock historical data response."""
        self.mock_responses['historical_data'] = candles
        return self
    
    def with_exception_on(self, method: str, exception: Exception) -> 'MockKiteClientBuilder':
        """Add exception to be raised on specific method call."""
        self.mock_exceptions[method] = exception
        return self
    
    def build(self) -> Mock:
        """Build and return the mock KiteClient."""
        mock_client = Mock()
        
        # Setup method responses
        if 'orders' in self.mock_responses:
            if 'get_orders' in self.mock_exceptions:
                mock_client.get_orders.side_effect = self.mock_exceptions['get_orders']
            else:
                mock_client.get_orders.return_value = self.mock_responses['orders']
        
        if 'positions' in self.mock_responses:
            if 'get_positions' in self.mock_exceptions:
                mock_client.get_positions.side_effect = self.mock_exceptions['get_positions']
            else:
                mock_client.get_positions.return_value = self.mock_responses['positions']
        
        if 'margins' in self.mock_responses:
            if 'get_margins' in self.mock_exceptions:
                mock_client.get_margins.side_effect = self.mock_exceptions['get_margins']
            else:
                mock_client.get_margins.return_value = self.mock_responses['margins']
        
        if 'profile' in self.mock_responses:
            if 'get_profile' in self.mock_exceptions:
                mock_client.get_profile.side_effect = self.mock_exceptions['get_profile']
            else:
                mock_client.get_profile.return_value = self.mock_responses['profile']
        
        if 'historical_data' in self.mock_responses:
            if 'get_historical_data' in self.mock_exceptions:
                mock_client.get_historical_data.side_effect = self.mock_exceptions['get_historical_data']
            else:
                mock_client.get_historical_data.return_value = self.mock_responses['historical_data']
        
        # Setup order placement
        if 'place_order' in self.mock_exceptions:
            mock_client.place_order.side_effect = self.mock_exceptions['place_order']
        else:
            mock_client.place_order.return_value = "TEST_ORDER_ID"
        
        # Setup order cancellation
        if 'cancel_order' in self.mock_exceptions:
            mock_client.cancel_order.side_effect = self.mock_exceptions['cancel_order']
        else:
            mock_client.cancel_order.return_value = "TEST_ORDER_ID"
        
        return mock_client


@contextmanager
def temporary_env_file(env_vars: Dict[str, str]) -> Generator[str, None, None]:
    """Create a temporary .env file with specified variables."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
        f.flush()
        
        try:
            yield f.name
        finally:
            os.unlink(f.name)


@contextmanager
def mock_streamlit_session_state(initial_state: Dict[str, Any] = None):
    """Mock Streamlit session state for testing."""
    if initial_state is None:
        initial_state = {}
    
    class MockSessionState:
        def __init__(self, initial_state):
            self._state = initial_state.copy()
        
        def __getattr__(self, key):
            return self._state.get(key)
        
        def __setattr__(self, key, value):
            if key.startswith('_'):
                super().__setattr__(key, value)
            else:
                self._state[key] = value
        
        def __contains__(self, key):
            return key in self._state
        
        def get(self, key, default=None):
            return self._state.get(key, default)
    
    mock_state = MockSessionState(initial_state)
    
    with patch('streamlit.session_state', mock_state):
        yield mock_state


class APITestHelper:
    """Helper class for API testing scenarios."""
    
    @staticmethod
    def create_mock_api_response(
        status_code: int = 200,
        data: Any = None,
        error_message: str = None
    ) -> Dict[str, Any]:
        """Create a mock API response structure."""
        response = {
            "status_code": status_code,
            "success": status_code == 200,
        }
        
        if data is not None:
            response["data"] = data
        
        if error_message is not None:
            response["error"] = error_message
        
        return response
    
    @staticmethod
    def simulate_network_delay(delay_seconds: float = 0.1):
        """Simulate network delay in tests."""
        import time
        time.sleep(delay_seconds)
    
    @staticmethod
    def create_rate_limit_exception() -> Exception:
        """Create a rate limiting exception for testing."""
        return Exception("Rate limit exceeded. Please try again later.")
    
    @staticmethod
    def create_authentication_exception() -> Exception:
        """Create an authentication exception for testing."""
        return Exception("Invalid API credentials")
    
    @staticmethod
    def create_connection_exception() -> Exception:
        """Create a connection exception for testing."""
        return Exception("Connection timeout")


class TestFileManager:
    """Utility for managing test files and cleanup."""
    
    def __init__(self):
        self.temp_files = []
        self.temp_dirs = []
    
    def create_temp_file(self, content: str = "", suffix: str = ".txt") -> str:
        """Create a temporary file and track it for cleanup."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(content)
            self.temp_files.append(f.name)
            return f.name
    
    def create_temp_dir(self) -> str:
        """Create a temporary directory and track it for cleanup."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def cleanup(self):
        """Clean up all temporary files and directories."""
        import shutil
        
        for file_path in self.temp_files:
            try:
                os.unlink(file_path)
            except OSError:
                pass
        
        for dir_path in self.temp_dirs:
            try:
                shutil.rmtree(dir_path)
            except OSError:
                pass
        
        self.temp_files.clear()
        self.temp_dirs.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
