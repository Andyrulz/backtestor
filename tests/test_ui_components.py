"""Tests for UI components with mocked data."""

import pytest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime, date
from tests.test_utils import TestDataFactory, MockKiteClientBuilder


class TestUIComponents:
    """Test UI components with mocked Streamlit."""

    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit functions for testing."""
        with patch('src.ui.components.st') as mock_st:
            # Setup common mock behaviors
            mock_st.columns.return_value = [Mock(), Mock()]
            mock_st.form.return_value.__enter__ = Mock(return_value=Mock())
            mock_st.form.return_value.__exit__ = Mock(return_value=None)
            mock_st.form_submit_button.return_value = False
            mock_st.selectbox.return_value = "NSE"
            mock_st.text_input.return_value = "RELIANCE"
            mock_st.number_input.return_value = 1
            yield mock_st

    def test_render_orders_table_with_data(self, mock_streamlit):
        """Test orders table rendering with sample data."""
        from src.ui.components import render_orders_table
        
        # Create test orders
        orders = [
            TestDataFactory.create_test_order(
                order_id="TEST123",
                tradingsymbol="RELIANCE",
                status="COMPLETE"
            ),
            TestDataFactory.create_test_order(
                order_id="TEST124",
                tradingsymbol="SBIN",
                status="OPEN"
            )
        ]
        
        # Render table
        render_orders_table(orders)
        
        # Verify dataframe was called
        mock_streamlit.dataframe.assert_called_once()

    def test_render_orders_table_empty(self, mock_streamlit):
        """Test orders table rendering with no data."""
        from src.ui.components import render_orders_table
        
        # Render empty table
        render_orders_table([])
        
        # Should show info message
        mock_streamlit.info.assert_called_with("No orders found for today")

    def test_render_positions_table_with_data(self, mock_streamlit):
        """Test positions table rendering with sample data."""
        from src.ui.components import render_positions_table
        
        # Create test positions
        positions = [
            TestDataFactory.create_test_position(
                tradingsymbol="RELIANCE",
                quantity=10,
                pnl=100.0
            ),
            TestDataFactory.create_test_position(
                tradingsymbol="SBIN",
                quantity=-5,
                pnl=-50.0
            )
        ]
        
        # Render table
        render_positions_table(positions)
        
        # Verify dataframe was called
        mock_streamlit.dataframe.assert_called_once()

    def test_render_positions_table_empty(self, mock_streamlit):
        """Test positions table rendering with no active positions."""
        from src.ui.components import render_positions_table
        
        # Create positions with zero quantity
        positions = [
            TestDataFactory.create_test_position(quantity=0)
        ]
        
        # Render table
        render_positions_table(positions)
        
        # Should show info message for no active positions
        mock_streamlit.info.assert_called_with("No active positions")

    def test_render_margins_info(self, mock_streamlit):
        """Test margins information rendering."""
        from src.ui.components import render_margins_info
        
        # Create test margins data
        margins = {
            "equity": {
                "available": {"cash": 50000.0},
                "net": 100000.0,
                "utilised": {"debits": 50000.0}
            },
            "commodity": {
                "available": {"cash": 25000.0},
                "net": 50000.0,
                "utilised": {"debits": 25000.0}
            }
        }
        
        # Setup mock columns
        col1_mock = Mock()
        col2_mock = Mock()
        mock_streamlit.columns.return_value = [col1_mock, col2_mock]
        
        # Render margins
        render_margins_info(margins)
        
        # Verify subheader was called
        mock_streamlit.subheader.assert_called_with("💰 Account Margins")
        
        # Verify columns were used
        mock_streamlit.columns.assert_called_with(2)

    def test_render_profile_info(self, mock_streamlit):
        """Test profile information rendering."""
        from src.ui.components import render_profile_info
        
        # Create test profile data
        profile = {
            "user_id": "TEST123",
            "user_name": "Test User",
            "email": "test@example.com",
            "broker": "ZERODHA",
            "exchanges": ["NSE", "BSE"],
            "products": ["CNC", "MIS"],
            "order_types": ["MARKET", "LIMIT"]
        }
        
        # Setup mock columns
        col1_mock = Mock()
        col2_mock = Mock()
        mock_streamlit.columns.return_value = [col1_mock, col2_mock]
        
        # Render profile
        render_profile_info(profile)
        
        # Verify subheader was called
        mock_streamlit.subheader.assert_called_with("👤 Profile Information")

    @patch('src.ui.components.st.form')
    def test_render_order_form_submit_validation(self, mock_form, mock_streamlit):
        """Test order form submission validation."""
        from src.ui.components import render_order_form
        
        # Setup form context manager
        form_context = Mock()
        mock_form.return_value.__enter__ = Mock(return_value=form_context)
        mock_form.return_value.__exit__ = Mock(return_value=None)
        
        # Setup form submission
        mock_streamlit.form_submit_button.return_value = True
        mock_streamlit.text_input.return_value = ""  # Empty trading symbol
        
        # Create mock client
        mock_client = Mock()
        
        # Render form
        render_order_form(mock_client)
        
        # Should show validation error for empty trading symbol
        mock_streamlit.error.assert_called_with("Trading symbol is required")

    def test_render_historical_data_form(self, mock_streamlit):
        """Test historical data form rendering."""
        from src.ui.components import render_historical_data
        
        # Setup mock columns
        mock_streamlit.columns.side_effect = [
            [Mock(), Mock(), Mock()],  # First row of columns
            [Mock(), Mock()]  # Second row of columns
        ]
        
        # Setup date inputs
        mock_streamlit.date_input.side_effect = [
            date(2024, 1, 1),  # from_date
            date(2024, 1, 31)  # to_date
        ]
        
        # Setup other inputs
        mock_streamlit.number_input.return_value = 738561
        mock_streamlit.selectbox.return_value = "day"
        mock_streamlit.button.return_value = False
        
        # Create mock client
        mock_client = Mock()
        
        # Render form
        render_historical_data(mock_client)
        
        # Verify subheader was called
        mock_streamlit.subheader.assert_called_with("📊 Historical Data")

    @patch('src.ui.components.st.form')
    def test_order_form_successful_submission(self, mock_form, mock_streamlit):
        """Test successful order form submission."""
        from src.ui.components import render_order_form
        
        # Setup form context manager
        form_context = Mock()
        mock_form.return_value.__enter__ = Mock(return_value=form_context)
        mock_form.return_value.__exit__ = Mock(return_value=None)
        
        # Setup successful form submission
        mock_streamlit.form_submit_button.return_value = True
        mock_streamlit.text_input.return_value = "RELIANCE"
        mock_streamlit.selectbox.side_effect = ["NSE", "BUY", "MARKET", "CNC"]
        mock_streamlit.number_input.side_effect = [1, 0.0, 0.0, 0]  # quantity, price, trigger_price, disclosed_quantity
        
        # Create mock client that returns order ID
        mock_client = Mock()
        mock_client.place_order.return_value = "ORDER123"
        
        # Setup spinner context
        spinner_context = Mock()
        mock_streamlit.spinner.return_value.__enter__ = Mock(return_value=spinner_context)
        mock_streamlit.spinner.return_value.__exit__ = Mock(return_value=None)
        
        # Render form
        render_order_form(mock_client)
        
        # Should show success message
        mock_streamlit.success.assert_called_with("Order placed successfully! Order ID: ORDER123")

    def test_historical_data_fetch_and_display(self, mock_streamlit):
        """Test historical data fetching and display."""
        from src.ui.components import render_historical_data
        
        # Setup mock inputs
        mock_streamlit.columns.side_effect = [
            [Mock(), Mock(), Mock()],  # First row
            [Mock(), Mock()]  # Second row
        ]
        mock_streamlit.number_input.return_value = 738561
        mock_streamlit.date_input.side_effect = [date(2024, 1, 1), date(2024, 1, 31)]
        mock_streamlit.selectbox.return_value = "day"
        mock_streamlit.button.return_value = True  # Fetch button clicked
        
        # Setup spinner context
        spinner_context = Mock()
        mock_streamlit.spinner.return_value.__enter__ = Mock(return_value=spinner_context)
        mock_streamlit.spinner.return_value.__exit__ = Mock(return_value=None)
        
        # Setup expandable section
        expander_context = Mock()
        mock_streamlit.expander.return_value.__enter__ = Mock(return_value=expander_context)
        mock_streamlit.expander.return_value.__exit__ = Mock(return_value=None)
        
        # Create mock client with historical data
        mock_client = Mock()
        test_candles = [
            TestDataFactory.create_test_candle(
                date_val=datetime(2024, 1, 1),
                open_price=2500.0
            )
        ]
        mock_client.get_historical_data.return_value = test_candles
        
        # Render component
        render_historical_data(mock_client)
        
        # Should show success message
        mock_streamlit.success.assert_called_with("Fetched 1 candles")
        
        # Should display chart
        mock_streamlit.line_chart.assert_called_once()


class TestUIComponentsErrorHandling:
    """Test error handling in UI components."""

    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit functions for error testing."""
        with patch('src.ui.components.st') as mock_st:
            mock_st.columns.return_value = [Mock(), Mock()]
            yield mock_st

    def test_order_form_api_error_handling(self, mock_streamlit):
        """Test order form API error handling."""
        from src.ui.components import render_order_form
        
        # Setup form with valid inputs but failing API
        with patch('src.ui.components.st.form'):
            mock_streamlit.form_submit_button.return_value = True
            mock_streamlit.text_input.return_value = "RELIANCE"
            mock_streamlit.selectbox.side_effect = ["NSE", "BUY", "MARKET", "CNC"]
            mock_streamlit.number_input.side_effect = [1, 0.0, 0.0, 0]
            
            # Create mock client that raises exception
            mock_client = Mock()
            mock_client.place_order.side_effect = Exception("API Error")
            
            # Setup spinner context
            spinner_context = Mock()
            mock_streamlit.spinner.return_value.__enter__ = Mock(return_value=spinner_context)
            mock_streamlit.spinner.return_value.__exit__ = Mock(return_value=None)
            
            # Render form
            render_order_form(mock_client)
            
            # Should show error message
            mock_streamlit.error.assert_called_with("Failed to place order: API Error")

    def test_historical_data_api_error_handling(self, mock_streamlit):
        """Test historical data API error handling."""
        from src.ui.components import render_historical_data
        
        # Setup inputs that trigger fetch
        mock_streamlit.columns.side_effect = [
            [Mock(), Mock(), Mock()],
            [Mock(), Mock()]
        ]
        mock_streamlit.number_input.return_value = 738561
        mock_streamlit.date_input.side_effect = [date(2024, 1, 1), date(2024, 1, 31)]
        mock_streamlit.selectbox.return_value = "day"
        mock_streamlit.button.return_value = True
        
        # Setup spinner context
        spinner_context = Mock()
        mock_streamlit.spinner.return_value.__enter__ = Mock(return_value=spinner_context)
        mock_streamlit.spinner.return_value.__exit__ = Mock(return_value=None)
        
        # Create mock client that raises exception
        mock_client = Mock()
        mock_client.get_historical_data.side_effect = Exception("Data fetch failed")
        
        # Render component
        render_historical_data(mock_client)
        
        # Should show error message
        mock_streamlit.error.assert_called_with("Failed to fetch historical data: Data fetch failed")
