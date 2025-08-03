"""Main Streamlit application for Kite trading system."""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import streamlit as st
import logging
from typing import Optional
from config import AppConfig
from kite.client import KiteClient
from auto_auth import render_auto_login, get_auto_authenticated_client
from ui.components import (
    render_order_form,
    render_orders_table,
    render_historical_data,
    render_positions_table,
    render_margins_info,
    render_profile_info,
)
# from ui.strategy_components import render_strategy_dashboard, render_strategy_management
# from strategies import StrategyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Page configuration
st.set_page_config(
    page_title="Kite Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_kite_client() -> Optional[KiteClient]:
    """Get cached Kite client instance.
    
    Returns:
        KiteClient instance or None if configuration fails
    """
    try:
        config = AppConfig.from_env()
        
        # Try to get auto-authenticated client
        kite_connect = get_auto_authenticated_client(config.kite)
        
        if kite_connect:
            # Test the connection
            try:
                kite_connect.profile()
                return KiteClient(
                    api_key=config.kite.api_key,
                    access_token=config.kite.access_token,
                    api_secret=config.kite.api_secret
                )
            except Exception as e:
                # Connection failed, token might be invalid
                st.error(f"Connection test failed: {e}")
                return None
        
        return None
        
    except Exception as e:
        st.error(f"Failed to initialize configuration: {str(e)}")
        st.info("Please check your .env file and ensure all required variables are set correctly.")
        return None


def main():
    """Main application function."""
    st.title("📈 Kite Trading System")
    st.markdown("A comprehensive trading interface for Zerodha Kite API")
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'auth_in_progress' not in st.session_state:
        st.session_state.auth_in_progress = False
    if 'strategy_manager' not in st.session_state:
        st.session_state.strategy_manager = None
    
    # Initialize configuration
    try:
        config = AppConfig.from_env()
    except Exception as e:
        st.error(f"Configuration error: {str(e)}")
        st.info("Please check your .env file and ensure all required variables are set correctly.")
        st.stop()
    
    # Try to get authenticated client
    kite_client = None
    
    # Direct authentication check - bypass session state complexity
    try:
        kite_connect = get_auto_authenticated_client(config.kite)
        if kite_connect:
            # Test the connection
            profile_test = kite_connect.profile()
            kite_client = KiteClient(
                api_key=config.kite.api_key,
                access_token=config.kite.access_token,
                api_secret=config.kite.api_secret
            )
            st.session_state.authenticated = True
            st.session_state.auth_in_progress = False
        else:
            # Clear any cached client
            get_kite_client.clear()
    except Exception as e:
        st.warning(f"Authentication check failed: {e}")
        get_kite_client.clear()
        kite_client = None
    
    # If not authenticated, show auto-login
    if not kite_client and not st.session_state.authenticated:
        if not st.session_state.auth_in_progress:
            st.session_state.auth_in_progress = True
            
        authenticated, kite_connect = render_auto_login(config.kite)
        
        if authenticated and kite_connect:
            # Clear cache and create our KiteClient wrapper
            get_kite_client.clear()
            st.session_state.authenticated = True
            st.session_state.auth_in_progress = False
            
            kite_client = KiteClient(
                api_key=config.kite.api_key,
                access_token=config.kite.access_token,
                api_secret=config.kite.api_secret
            )
        else:
            st.stop()
    elif st.session_state.authenticated and not kite_client:
        # Re-create client after successful auth
        kite_client = KiteClient(
            api_key=config.kite.api_key,
            access_token=config.kite.access_token,
            api_secret=config.kite.api_secret
        )
    
    # Mark as authenticated if we have a working client
    if kite_client:
        st.session_state.authenticated = True
        st.session_state.auth_in_progress = False
        
        # Initialize strategy manager
        # if st.session_state.strategy_manager is None:
        #     st.session_state.strategy_manager = StrategyManager(kite_client)
    
    # Show user info and logout option in sidebar
    with st.sidebar:
        st.title("🔐 Session")
        try:
            profile = kite_client.get_profile()
            user_name = profile.get('user_name', 'Unknown')
            user_id = profile.get('user_id', 'N/A')
            
            st.success(f"✅ **{user_name}**")
            st.caption(f"ID: {user_id}")
            
            # Session info
            from pathlib import Path
            import time
            token_file = Path(__file__).parent.parent / ".kite_session"
            if token_file.exists():
                try:
                    with open(token_file, 'r') as f:
                        token_data = f.read().strip().split('|')
                        if len(token_data) >= 2:
                            timestamp = float(token_data[1])
                            hours_left = 24 - ((time.time() - timestamp) / 3600)
                            if hours_left > 0:
                                st.info(f"⏰ Session: {hours_left:.1f}h left")
                except Exception:
                    pass
            
            st.divider()
            
            if st.button("🚪 Logout", type="secondary", use_container_width=True):
                # Clear access token and session file
                import os
                env_path = Path(__file__).parent.parent / ".env"
                
                if env_path.exists():
                    with open(env_path, 'r') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines):
                        if line.startswith("KITE_ACCESS_TOKEN="):
                            lines[i] = "KITE_ACCESS_TOKEN=\n"
                            break
                    
                    with open(env_path, 'w') as f:
                        f.writelines(lines)
                
                # Remove session file
                if token_file.exists():
                    token_file.unlink()
                
                # Clear cache and session state
                get_kite_client.clear()
                st.session_state.authenticated = False
                st.session_state.auth_in_progress = False
                
                st.success("Logged out successfully!")
                st.rerun()
                
        except Exception as e:
            st.error(f"Session error: {str(e)}")
    
    # Horizontal navigation using tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🏠 Dashboard",
        "📈 Place Order", 
        "📋 Orders",
        "📊 Historical Data",
        "💼 Positions",
        "💰 Margins",
        "👤 Profile"
    ])
    
    # Main content area
    try:
        with tab1:
            render_dashboard(kite_client)
        with tab2:
            render_order_form(kite_client)
        with tab3:
            render_orders_page(kite_client)
        with tab4:
            render_historical_data(kite_client)
        with tab5:
            render_positions_page(kite_client)
        with tab6:
            render_margins_page(kite_client)
        with tab7:
            render_profile_page(kite_client)
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("This might be due to an expired session. Please try logging out and logging back in.")
        if st.button("🔄 Refresh"):
            st.rerun()


def render_dashboard(kite_client: KiteClient):
    """Render the dashboard page.
    
    Args:
        kite_client: Kite client instance
    """
    st.header("🏠 Dashboard")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Get basic information
        with st.spinner("Loading dashboard data..."):
            orders = kite_client.get_orders()
            positions = kite_client.get_positions()
            margins = kite_client.get_margins()
        
        with col1:
            total_orders = len(orders)
            st.metric("Today's Orders", total_orders)
        
        with col2:
            active_positions = len([p for p in positions if p.quantity != 0])
            st.metric("Active Positions", active_positions)
        
        with col3:
            equity_available = margins.get("equity", {}).get("available", {}).get("cash", 0)
            st.metric("Available Cash", f"₹{equity_available:,.2f}")
        
        with col4:
            total_pnl = sum(p.pnl for p in positions if p.quantity != 0)
            st.metric("Total P&L", f"₹{total_pnl:,.2f}")
        
        # Recent orders
        st.subheader("📋 Recent Orders")
        recent_orders = orders[:5] if orders else []
        render_orders_table(recent_orders)
        
        # Current positions
        st.subheader("💼 Current Positions")
        active_positions_list = [p for p in positions if p.quantity != 0]
        render_positions_table(active_positions_list)
        
    except Exception as e:
        st.error(f"Failed to load dashboard data: {str(e)}")


def render_orders_page(kite_client: KiteClient):
    """Render the orders page.
    
    Args:
        kite_client: Kite client instance
    """
    st.header("📋 Orders")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh Orders", type="primary"):
            st.rerun()
    
    try:
        with st.spinner("Loading orders..."):
            orders = kite_client.get_orders()
        
        render_orders_table(orders)
        
        # Order cancellation
        if orders:
            st.subheader("Cancel Order")
            order_ids = [f"{order.order_id} - {order.tradingsymbol}" for order in orders if order.status == "OPEN"]
            
            if order_ids:
                selected_order = st.selectbox("Select order to cancel", order_ids)
                if st.button("Cancel Selected Order", type="secondary"):
                    order_id = selected_order.split(" - ")[0]
                    try:
                        kite_client.cancel_order(order_id)
                        st.success(f"Order {order_id} cancelled successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to cancel order: {str(e)}")
            else:
                st.info("No open orders to cancel")
        
    except Exception as e:
        st.error(f"Failed to load orders: {str(e)}")


def render_positions_page(kite_client: KiteClient):
    """Render the positions page.
    
    Args:
        kite_client: Kite client instance
    """
    st.header("💼 Positions")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh Positions", type="primary"):
            st.rerun()
    
    try:
        with st.spinner("Loading positions..."):
            positions = kite_client.get_positions()
        
        render_positions_table(positions)
        
    except Exception as e:
        st.error(f"Failed to load positions: {str(e)}")


def render_margins_page(kite_client: KiteClient):
    """Render the margins page.
    
    Args:
        kite_client: Kite client instance
    """
    st.header("💰 Margins")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Refresh Margins", type="primary"):
            st.rerun()
    
    try:
        with st.spinner("Loading margin data..."):
            margins = kite_client.get_margins()
        
        render_margins_info(margins)
        
        # Raw margin data
        with st.expander("View Raw Margin Data"):
            st.json(margins)
        
    except Exception as e:
        st.error(f"Failed to load margin data: {str(e)}")


def render_profile_page(kite_client: KiteClient):
    """Render the profile page.
    
    Args:
        kite_client: Kite client instance
    """
    st.header("👤 Profile")
    
    try:
        with st.spinner("Loading profile data..."):
            profile = kite_client.get_profile()
        
        render_profile_info(profile)
        
        # Raw profile data
        with st.expander("View Raw Profile Data"):
            st.json(profile)
        
    except Exception as e:
        st.error(f"Failed to load profile data: {str(e)}")


if __name__ == "__main__":
    main()
