"""UI components for the Kite trading system."""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from typing import List, Optional
from kite.models import (
    OrderRequest,
    Order,
    Candle,
    Position,
    OrderType,
    TransactionType,
    ProductType,
    Exchange,
)
from kite.client import KiteClient


def render_order_form(kite_client: KiteClient) -> None:
    """Render the order placement form.
    
    Args:
        kite_client: Kite client instance
    """
    st.subheader("📈 Place Order")
    
    with st.form("order_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            tradingsymbol = st.text_input(
                "Trading Symbol", 
                value="RELIANCE",
                help="Enter the trading symbol (e.g., RELIANCE, SBIN)"
            )
            
            exchange = st.selectbox(
                "Exchange",
                options=[e.value for e in Exchange],
                index=0,
                help="Select the exchange"
            )
            
            transaction_type = st.selectbox(
                "Transaction Type",
                options=[t.value for t in TransactionType],
                help="Buy or Sell"
            )
            
            order_type = st.selectbox(
                "Order Type",
                options=[o.value for o in OrderType],
                help="Market, Limit, SL, or SL-M"
            )
        
        with col2:
            quantity = st.number_input(
                "Quantity",
                min_value=1,
                value=1,
                help="Number of shares/lots"
            )
            
            product = st.selectbox(
                "Product Type",
                options=[p.value for p in ProductType],
                help="CNC (Delivery), MIS (Intraday), NRML (Normal)"
            )
            
            price = st.number_input(
                "Price",
                min_value=0.0,
                value=0.0,
                format="%.2f",
                help="Price per unit (0 for market orders)"
            )
            
            trigger_price = st.number_input(
                "Trigger Price",
                min_value=0.0,
                value=0.0,
                format="%.2f",
                help="Trigger price for SL orders"
            )
        
        # Optional fields
        with st.expander("Advanced Options"):
            tag = st.text_input(
                "Tag",
                help="Optional tag for the order"
            )
            
            disclosed_quantity = st.number_input(
                "Disclosed Quantity",
                min_value=0,
                value=0,
                help="Disclosed quantity (0 for no disclosure)"
            )
        
        submitted = st.form_submit_button("Place Order", type="primary")
        
        if submitted:
            try:
                # Validate inputs
                if not tradingsymbol:
                    st.error("Trading symbol is required")
                    return
                
                if order_type in [OrderType.LIMIT.value, OrderType.SL.value] and price <= 0:
                    st.error("Price is required for LIMIT and SL orders")
                    return
                
                if order_type in [OrderType.SL.value, OrderType.SL_M.value] and trigger_price <= 0:
                    st.error("Trigger price is required for SL orders")
                    return
                
                # Create order request
                order_request = OrderRequest(
                    tradingsymbol=tradingsymbol.upper(),
                    exchange=Exchange(exchange),
                    transaction_type=TransactionType(transaction_type),
                    order_type=OrderType(order_type),
                    quantity=quantity,
                    product=ProductType(product),
                    price=price if price > 0 else None,
                    trigger_price=trigger_price if trigger_price > 0 else None,
                    tag=tag if tag else None,
                    disclosed_quantity=disclosed_quantity if disclosed_quantity > 0 else None,
                )
                
                # Place order
                with st.spinner("Placing order..."):
                    order_id = kite_client.place_order(order_request)
                    st.success(f"Order placed successfully! Order ID: {order_id}")
                    
            except Exception as e:
                st.error(f"Failed to place order: {str(e)}")


def render_orders_table(orders: List[Order]) -> None:
    """Render orders in a table format.
    
    Args:
        orders: List of orders to display
    """
    if not orders:
        st.info("No orders found for today")
        return
    
    # Convert orders to DataFrame for better display
    orders_data = []
    for order in orders:
        orders_data.append({
            "Order ID": order.order_id,
            "Symbol": order.tradingsymbol,
            "Exchange": order.exchange,
            "Type": f"{order.transaction_type} {order.order_type}",
            "Product": order.product,
            "Quantity": order.quantity,
            "Price": f"₹{order.price:.2f}" if order.price else "Market",
            "Status": order.status,
            "Filled": order.filled_quantity,
            "Pending": order.pending_quantity,
            "Time": order.order_timestamp.strftime("%H:%M:%S"),
        })
    
    df = pd.DataFrame(orders_data)
    
    # Apply styling based on status
    def style_status(val):
        if val == "COMPLETE":
            return "background-color: #d4edda; color: #155724"
        elif val == "CANCELLED":
            return "background-color: #f8d7da; color: #721c24"
        elif val == "OPEN":
            return "background-color: #fff3cd; color: #856404"
        return ""
    
    styled_df = df.style.applymap(style_status, subset=["Status"])
    st.dataframe(styled_df, use_container_width=True)


def render_historical_data(kite_client: KiteClient) -> None:
    """Render historical data form and chart.
    
    Args:
        kite_client: Kite client instance
    """
    st.subheader("📊 Historical Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        instrument_token = st.number_input(
            "Instrument Token",
            value=738561,
            help="Enter instrument token (e.g., 738561 for RELIANCE)"
        )
    
    with col2:
        from_date = st.date_input(
            "From Date",
            value=date.today() - timedelta(days=30),
            max_value=date.today()
        )
    
    with col3:
        to_date = st.date_input(
            "To Date",
            value=date.today(),
            max_value=date.today()
        )
    
    col4, col5 = st.columns(2)
    
    with col4:
        interval = st.selectbox(
            "Interval",
            options=["minute", "3minute", "5minute", "15minute", "30minute", "60minute", "day"],
            index=6,
            help="Candle interval"
        )
    
    with col5:
        if st.button("Fetch Data", type="primary"):
            try:
                with st.spinner("Fetching historical data..."):
                    candles = kite_client.get_historical_data(
                        instrument_token=instrument_token,
                        from_date=from_date,
                        to_date=to_date,
                        interval=interval
                    )
                
                if candles:
                    # Convert to DataFrame
                    candles_data = []
                    for candle in candles:
                        candles_data.append({
                            "Date": candle.date,
                            "Open": candle.open,
                            "High": candle.high,
                            "Low": candle.low,
                            "Close": candle.close,
                            "Volume": candle.volume,
                        })
                    
                    df = pd.DataFrame(candles_data)
                    df["Date"] = pd.to_datetime(df["Date"])
                    
                    # Display chart
                    st.line_chart(df.set_index("Date")[["Open", "High", "Low", "Close"]])
                    
                    # Display data table
                    with st.expander("View Raw Data"):
                        st.dataframe(df, use_container_width=True)
                    
                    st.success(f"Fetched {len(candles)} candles")
                else:
                    st.warning("No data found for the specified parameters")
                    
            except Exception as e:
                st.error(f"Failed to fetch historical data: {str(e)}")


def render_positions_table(positions: List[Position]) -> None:
    """Render positions in a table format.
    
    Args:
        positions: List of positions to display
    """
    if not positions:
        st.info("No positions found")
        return
    
    # Convert positions to DataFrame
    positions_data = []
    for position in positions:
        if position.quantity != 0:  # Only show non-zero positions
            positions_data.append({
                "Symbol": position.tradingsymbol,
                "Exchange": position.exchange,
                "Product": position.product,
                "Quantity": position.quantity,
                "Avg Price": f"₹{position.average_price:.2f}",
                "LTP": f"₹{position.last_price:.2f}",
                "P&L": f"₹{position.pnl:.2f}",
                "M2M": f"₹{position.m2m:.2f}",
                "Value": f"₹{position.value:.2f}",
            })
    
    if positions_data:
        df = pd.DataFrame(positions_data)
        
        # Apply styling for P&L
        def style_pnl(val):
            val_num = float(val.replace("₹", "").replace(",", ""))
            if val_num > 0:
                return "background-color: #d4edda; color: #155724"
            elif val_num < 0:
                return "background-color: #f8d7da; color: #721c24"
            return ""
        
        styled_df = df.style.applymap(style_pnl, subset=["P&L", "M2M"])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("No active positions")


def render_margins_info(margins: dict) -> None:
    """Render margin information.
    
    Args:
        margins: Margin data dictionary
    """
    st.subheader("💰 Account Margins")
    
    equity_margins = margins.get("equity", {})
    commodity_margins = margins.get("commodity", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Equity")
        if equity_margins:
            st.metric("Available Cash", f"₹{equity_margins.get('available', {}).get('cash', 0):,.2f}")
            st.metric("Total", f"₹{equity_margins.get('net', 0):,.2f}")
            st.metric("Used", f"₹{equity_margins.get('utilised', {}).get('debits', 0):,.2f}")
    
    with col2:
        st.markdown("#### Commodity")
        if commodity_margins:
            st.metric("Available Cash", f"₹{commodity_margins.get('available', {}).get('cash', 0):,.2f}")
            st.metric("Total", f"₹{commodity_margins.get('net', 0):,.2f}")
            st.metric("Used", f"₹{commodity_margins.get('utilised', {}).get('debits', 0):,.2f}")


def render_profile_info(profile: dict) -> None:
    """Render user profile information.
    
    Args:
        profile: User profile data dictionary
    """
    st.subheader("👤 Profile Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**User ID:** {profile.get('user_id', 'N/A')}")
        st.info(f"**Name:** {profile.get('user_name', 'N/A')}")
        st.info(f"**Email:** {profile.get('email', 'N/A')}")
    
    with col2:
        st.info(f"**Broker:** {profile.get('broker', 'N/A')}")
        st.info(f"**Exchanges:** {', '.join(profile.get('exchanges', []))}")
        st.info(f"**Products:** {', '.join(profile.get('products', []))}")
    
    # Order types
    order_types = profile.get('order_types', [])
    if order_types:
        st.info(f"**Available Order Types:** {', '.join(order_types)}")
