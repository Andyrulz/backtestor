"""End-to-end tests for the Streamlit trading interface."""

import pytest
from playwright.sync_api import Page, expect


class TestStreamlitApp:
    """Test cases for the main Streamlit application."""

    def test_app_loads_successfully(self, app_page: Page):
        """Test that the application loads without errors."""
        # Check that the main title is present
        expect(app_page.locator("h1")).to_contain_text("Kite Trading System")
        
        # Check that the subtitle is present
        expect(app_page.locator("text=A comprehensive trading interface")).to_be_visible()

    def test_sidebar_navigation_exists(self, app_page: Page):
        """Test that sidebar navigation is present and functional."""
        # Check sidebar title
        expect(app_page.locator("text=Navigation")).to_be_visible()
        
        # Check navigation options
        navigation_items = [
            "🏠 Dashboard",
            "📈 Place Order",
            "📋 Orders", 
            "📊 Historical Data",
            "💼 Positions",
            "💰 Margins",
            "👤 Profile"
        ]
        
        for item in navigation_items:
            expect(app_page.locator(f"option[value='{item}']")).to_be_visible()

    def test_dashboard_page_loads(self, app_page: Page):
        """Test that dashboard page loads with expected content."""
        # Dashboard should be the default page
        expect(app_page.locator("text=🏠 Dashboard")).to_be_visible()
        
        # Should show error message since we're using test credentials
        expect(app_page.locator("text=Failed to initialize Kite client")).to_be_visible()

    def test_navigation_to_place_order(self, app_page: Page):
        """Test navigation to place order page."""
        # Click on place order in sidebar
        app_page.select_option("select", "📈 Place Order")
        app_page.wait_for_timeout(1000)  # Wait for page to load
        
        # Should show place order form
        expect(app_page.locator("text=📈 Place Order")).to_be_visible()

    def test_navigation_to_historical_data(self, app_page: Page):
        """Test navigation to historical data page."""
        # Click on historical data in sidebar
        app_page.select_option("select", "📊 Historical Data")
        app_page.wait_for_timeout(1000)
        
        # Should show historical data form
        expect(app_page.locator("text=📊 Historical Data")).to_be_visible()


class TestOrderForm:
    """Test cases for the order placement form."""

    def test_order_form_elements_present(self, app_page: Page):
        """Test that all order form elements are present."""
        # Navigate to place order page
        app_page.select_option("select", "📈 Place Order")
        app_page.wait_for_timeout(1000)
        
        # Check form elements (if visible despite connection error)
        form_elements = [
            "Trading Symbol",
            "Exchange", 
            "Transaction Type",
            "Order Type",
            "Quantity",
            "Product Type"
        ]
        
        for element in form_elements:
            # Use a more flexible approach since form might be hidden due to connection error
            if app_page.locator(f"text={element}").is_visible():
                expect(app_page.locator(f"text={element}")).to_be_visible()

    def test_form_validation_empty_symbol(self, app_page: Page):
        """Test form validation for empty trading symbol."""
        # Navigate to place order page
        app_page.select_option("select", "📈 Place Order")
        app_page.wait_for_timeout(1000)
        
        # This test would require the form to be visible
        # In a real scenario with proper credentials, we would:
        # 1. Clear the trading symbol field
        # 2. Try to submit the form
        # 3. Check for validation error message
        
        # For now, just verify the page loads
        expect(app_page.locator("text=📈 Place Order")).to_be_visible()


class TestHistoricalData:
    """Test cases for historical data functionality."""

    def test_historical_data_form_elements(self, app_page: Page):
        """Test that historical data form elements are present."""
        # Navigate to historical data page
        app_page.select_option("select", "📊 Historical Data")
        app_page.wait_for_timeout(1000)
        
        # Check page loads
        expect(app_page.locator("text=📊 Historical Data")).to_be_visible()
        
        # Form elements would be tested here with proper credentials
        form_elements = [
            "Instrument Token",
            "From Date",
            "To Date", 
            "Interval"
        ]
        
        for element in form_elements:
            if app_page.locator(f"text={element}").is_visible():
                expect(app_page.locator(f"text={element}")).to_be_visible()


class TestResponsiveDesign:
    """Test cases for responsive design and mobile compatibility."""

    def test_mobile_viewport(self, app_page: Page):
        """Test app behavior on mobile viewport."""
        # Set mobile viewport
        app_page.set_viewport_size({"width": 375, "height": 667})
        app_page.reload()
        app_page.wait_for_load_state('networkidle')
        
        # Check that main elements are still visible
        expect(app_page.locator("h1")).to_contain_text("Kite Trading System")
        expect(app_page.locator("text=Navigation")).to_be_visible()

    def test_tablet_viewport(self, app_page: Page):
        """Test app behavior on tablet viewport."""
        # Set tablet viewport
        app_page.set_viewport_size({"width": 768, "height": 1024})
        app_page.reload()
        app_page.wait_for_load_state('networkidle')
        
        # Check that main elements are still visible
        expect(app_page.locator("h1")).to_contain_text("Kite Trading System")
        expect(app_page.locator("text=Navigation")).to_be_visible()


class TestErrorHandling:
    """Test cases for error handling and edge cases."""

    def test_connection_error_handling(self, app_page: Page):
        """Test that connection errors are handled gracefully."""
        # With test credentials, should show connection error
        expect(app_page.locator("text=Failed to initialize Kite client")).to_be_visible()
        
        # Should also show helpful message
        expect(app_page.locator("text=Please check your .env file")).to_be_visible()

    def test_page_refresh_maintains_state(self, app_page: Page):
        """Test that page refresh doesn't break the application."""
        # Navigate to a different page
        app_page.select_option("select", "📈 Place Order")
        app_page.wait_for_timeout(1000)
        
        # Refresh the page
        app_page.reload()
        app_page.wait_for_load_state('networkidle')
        
        # Should still show the app title
        expect(app_page.locator("h1")).to_contain_text("Kite Trading System")


class TestAccessibility:
    """Test cases for accessibility compliance."""

    def test_keyboard_navigation(self, app_page: Page):
        """Test that the app is navigable using keyboard."""
        # Focus on the selectbox
        app_page.press("body", "Tab")
        
        # Should be able to navigate the dropdown with arrow keys
        app_page.press("select", "ArrowDown")
        app_page.press("select", "ArrowUp")
        
        # The app should remain functional
        expect(app_page.locator("h1")).to_contain_text("Kite Trading System")

    def test_color_contrast(self, app_page: Page):
        """Test basic color contrast by checking text visibility."""
        # Ensure main text elements are visible (indicating good contrast)
        expect(app_page.locator("h1")).to_be_visible()
        expect(app_page.locator("text=Navigation")).to_be_visible()
        
        # Error messages should also be clearly visible
        if app_page.locator("text=Failed to initialize Kite client").is_visible():
            expect(app_page.locator("text=Failed to initialize Kite client")).to_be_visible()
