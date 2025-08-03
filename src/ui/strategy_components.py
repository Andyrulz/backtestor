"""Strategy management UI components."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from strategies import (
    StrategyManager, StrategyConfig, MovingAverageCrossover, 
    RSIStrategy, BollingerBandsStrategy, MACDStrategy,
    StrategySignal, StrategyStatus
)
from kite.client import KiteClient


def render_strategy_dashboard(kite_client: KiteClient, strategy_manager: StrategyManager):
    """Render the strategy management dashboard.
    
    Args:
        kite_client: Kite client instance
        strategy_manager: Strategy manager instance
    """
    st.subheader("🤖 Strategy Dashboard")
    
    # Control panel
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("▶️ Start All", type="primary"):
            strategy_manager.start_all_strategies()
            st.success("All strategies started!")
            st.rerun()
    
    with col2:
        if st.button("⏸️ Stop All", type="secondary"):
            strategy_manager.stop_all_strategies()
            st.warning("All strategies stopped!")
            st.rerun()
    
    with col3:
        auto_execute = st.checkbox("🔄 Auto Execute", value=strategy_manager.auto_execute)
        if auto_execute != strategy_manager.auto_execute:
            strategy_manager.set_auto_execute(auto_execute)
    
    with col4:
        if st.button("🚨 Emergency Stop", type="secondary"):
            strategy_manager.emergency_stop()
            st.error("Emergency stop executed!")
            st.rerun()
    
    # Strategy status overview
    st.subheader("📊 Strategy Status")
    status_data = strategy_manager.get_strategy_status()
    
    if status_data:
        status_df = pd.DataFrame(status_data)
        
        # Color code status
        def style_status(val):
            color = {
                'ACTIVE': 'background-color: #90EE90',
                'STOPPED': 'background-color: #FFB6C1', 
                'PAUSED': 'background-color: #FFE4B5',
                'ERROR': 'background-color: #FF6B6B'
            }.get(val, '')
            return color
        
        styled_df = status_df.style.applymap(style_status, subset=['status'])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("No strategies configured. Add strategies using the 'Manage Strategies' tab.")
    
    # Recent signals
    st.subheader("📡 Recent Signals")
    signals = strategy_manager.get_all_signals()
    
    if signals:
        signal_rows = []
        for strategy_name, strategy_signals in signals.items():
            for symbol, signal in strategy_signals.items():
                signal_rows.append({
                    'Strategy': strategy_name,
                    'Symbol': symbol,
                    'Signal': signal.signal.value,
                    'Confidence': f"{signal.confidence:.2%}",
                    'Price': f"₹{signal.entry_price:.2f}" if signal.entry_price else "N/A",
                    'Timestamp': signal.timestamp.strftime("%H:%M:%S")
                })
        
        if signal_rows:
            signals_df = pd.DataFrame(signal_rows)
            st.dataframe(signals_df, use_container_width=True)
    else:
        st.info("No recent signals available")
    
    # Execution history
    st.subheader("📈 Recent Executions")
    executions = strategy_manager.get_recent_executions(limit=20)
    
    if executions:
        exec_rows = []
        for exec in executions:
            exec_rows.append({
                'Strategy': exec.strategy_name,
                'Symbol': exec.symbol,
                'Signal': exec.signal.signal.value,
                'Order ID': exec.order_id or "N/A",
                'Price': f"₹{exec.executed_price:.2f}" if exec.executed_price else "N/A",
                'Status': exec.status,
                'Time': exec.execution_time.strftime("%Y-%m-%d %H:%M:%S") if exec.execution_time else "N/A"
            })
        
        exec_df = pd.DataFrame(exec_rows)
        st.dataframe(exec_df, use_container_width=True)
    else:
        st.info("No executions yet")


def render_strategy_management(kite_client: KiteClient, strategy_manager: StrategyManager):
    """Render strategy management interface.
    
    Args:
        kite_client: Kite client instance
        strategy_manager: Strategy manager instance
    """
    st.subheader("⚙️ Strategy Management")
    
    # Strategy creation
    with st.expander("➕ Add New Strategy", expanded=False):
        render_strategy_creator(kite_client, strategy_manager)
    
    # Existing strategies
    st.subheader("📋 Existing Strategies")
    
    for strategy_name, strategy in strategy_manager.strategies.items():
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                st.write(f"**{strategy_name}** ({strategy.status.value})")
                st.caption(f"Symbols: {', '.join(strategy.config.symbols)}")
            
            with col2:
                if strategy.status == StrategyStatus.STOPPED:
                    if st.button("▶️ Start", key=f"start_{strategy_name}"):
                        strategy_manager.start_strategy(strategy_name)
                        st.rerun()
                else:
                    if st.button("⏸️ Stop", key=f"stop_{strategy_name}"):
                        strategy_manager.stop_strategy(strategy_name)
                        st.rerun()
            
            with col3:
                if st.button("📊 Analyze", key=f"analyze_{strategy_name}"):
                    signals = strategy.run_analysis()
                    st.session_state[f'signals_{strategy_name}'] = signals
                    st.rerun()
            
            with col4:
                if st.button("📈 Chart", key=f"chart_{strategy_name}"):
                    st.session_state[f'show_chart_{strategy_name}'] = True
                    st.rerun()
            
            with col5:
                if st.button("🗑️ Remove", key=f"remove_{strategy_name}"):
                    strategy_manager.remove_strategy(strategy_name)
                    st.rerun()
            
            # Show signals if available
            if f'signals_{strategy_name}' in st.session_state:
                signals = st.session_state[f'signals_{strategy_name}']
                if signals:
                    signal_cols = st.columns(len(signals))
                    for i, (symbol, signal) in enumerate(signals.items()):
                        with signal_cols[i]:
                            signal_color = {
                                'BUY': '🟢',
                                'SELL': '🔴', 
                                'HOLD': '🟡'
                            }.get(signal.signal.value, '⚪')
                            st.metric(
                                label=f"{signal_color} {symbol}",
                                value=signal.signal.value,
                                delta=f"{signal.confidence:.1%}"
                            )
            
            # Show chart if requested
            if f'show_chart_{strategy_name}' in st.session_state:
                render_strategy_chart(strategy, strategy_name)
                if st.button("❌ Close Chart", key=f"close_chart_{strategy_name}"):
                    del st.session_state[f'show_chart_{strategy_name}']
                    st.rerun()
            
            st.divider()


def render_strategy_creator(kite_client: KiteClient, strategy_manager: StrategyManager):
    """Render strategy creation form.
    
    Args:
        kite_client: Kite client instance
        strategy_manager: Strategy manager instance
    """
    with st.form("strategy_creation"):
        col1, col2 = st.columns(2)
        
        with col1:
            strategy_name = st.text_input("Strategy Name", placeholder="My Strategy")
            strategy_type = st.selectbox(
                "Strategy Type",
                ["Moving Average Crossover", "RSI Mean Reversion", "Bollinger Bands", "MACD Momentum"]
            )
            
            symbols_input = st.text_area(
                "Trading Symbols", 
                value="RELIANCE,TCS,HDFCBANK",
                help="Comma-separated list of symbols"
            )
            
            timeframe = st.selectbox(
                "Timeframe",
                ["5minute", "15minute", "30minute", "60minute", "day"],
                index=0
            )
        
        with col2:
            capital = st.number_input("Capital", value=100000.0, min_value=1000.0, step=1000.0)
            risk_per_trade = st.slider("Risk per Trade (%)", 1, 10, 2) / 100
            stop_loss_pct = st.slider("Stop Loss (%)", 1, 10, 5) / 100
            take_profit_pct = st.slider("Take Profit (%)", 5, 20, 10) / 100
            max_positions = st.number_input("Max Positions", value=3, min_value=1, max_value=10)
        
        # Strategy-specific parameters
        st.subheader("Strategy Parameters")
        params = {}
        
        if strategy_type == "Moving Average Crossover":
            col1, col2 = st.columns(2)
            with col1:
                params['fast_period'] = st.number_input("Fast MA Period", value=10, min_value=5, max_value=50)
            with col2:
                params['slow_period'] = st.number_input("Slow MA Period", value=20, min_value=10, max_value=100)
                
        elif strategy_type == "RSI Mean Reversion":
            col1, col2, col3 = st.columns(3)
            with col1:
                params['rsi_period'] = st.number_input("RSI Period", value=14, min_value=5, max_value=30)
            with col2:
                params['oversold'] = st.number_input("Oversold Level", value=30.0, min_value=10.0, max_value=40.0)
            with col3:
                params['overbought'] = st.number_input("Overbought Level", value=70.0, min_value=60.0, max_value=90.0)
                
        elif strategy_type == "Bollinger Bands":
            col1, col2 = st.columns(2)
            with col1:
                params['bb_period'] = st.number_input("BB Period", value=20, min_value=10, max_value=50)
            with col2:
                params['bb_std'] = st.number_input("Standard Deviation", value=2.0, min_value=1.0, max_value=3.0, step=0.1)
                
        elif strategy_type == "MACD Momentum":
            col1, col2, col3 = st.columns(3)
            with col1:
                params['fast'] = st.number_input("Fast EMA", value=12, min_value=5, max_value=20)
            with col2:
                params['slow'] = st.number_input("Slow EMA", value=26, min_value=20, max_value=50)
            with col3:
                params['signal_period'] = st.number_input("Signal Period", value=9, min_value=5, max_value=15)
        
        submitted = st.form_submit_button("Create Strategy", type="primary")
        
        if submitted:
            if not strategy_name:
                st.error("Please provide a strategy name")
                return
            
            if strategy_name in strategy_manager.strategies:
                st.error("Strategy name already exists")
                return
            
            symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
            if not symbols:
                st.error("Please provide at least one symbol")
                return
            
            # Create configuration
            config = StrategyConfig(
                name=strategy_name,
                symbols=symbols,
                timeframe=timeframe,
                capital=capital,
                max_positions=max_positions,
                risk_per_trade=risk_per_trade,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct
            )
            
            # Create strategy instance
            strategy_class_map = {
                "Moving Average Crossover": MovingAverageCrossover,
                "RSI Mean Reversion": RSIStrategy,
                "Bollinger Bands": BollingerBandsStrategy,
                "MACD Momentum": MACDStrategy
            }
            
            strategy_class = strategy_class_map[strategy_type]
            strategy = strategy_class(config, kite_client, **params)
            
            # Add to manager
            strategy_manager.add_strategy(strategy)
            
            st.success(f"Strategy '{strategy_name}' created successfully!")
            st.rerun()


def render_strategy_chart(strategy, strategy_name: str):
    """Render strategy analysis chart.
    
    Args:
        strategy: Strategy instance
        strategy_name: Name of the strategy
    """
    st.subheader(f"📈 {strategy_name} - Technical Analysis")
    
    if not strategy.config.symbols:
        st.warning("No symbols configured for this strategy")
        return
    
    symbol = st.selectbox("Select Symbol", strategy.config.symbols, key=f"chart_symbol_{strategy_name}")
    
    # Get data
    data = strategy.get_historical_data(symbol, days=60)
    
    if data.empty:
        st.warning(f"No data available for {symbol}")
        return
    
    # Create chart based on strategy type
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=[f'{symbol} Price & Indicators', 'Indicator Details'],
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3]
    )
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name='Price'
        ),
        row=1, col=1
    )
    
    # Add strategy-specific indicators
    if isinstance(strategy, MovingAverageCrossover):
        # Add moving averages
        data['fast_ma'] = data['close'].rolling(strategy.fast_period).mean()
        data['slow_ma'] = data['close'].rolling(strategy.slow_period).mean()
        
        fig.add_trace(
            go.Scatter(x=data.index, y=data['fast_ma'], name=f'Fast MA ({strategy.fast_period})', line=dict(color='blue')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=data.index, y=data['slow_ma'], name=f'Slow MA ({strategy.slow_period})', line=dict(color='red')),
            row=1, col=1
        )
        
        # Show difference in subplot
        fig.add_trace(
            go.Scatter(x=data.index, y=data['fast_ma'] - data['slow_ma'], name='MA Difference'),
            row=2, col=1
        )
    
    elif isinstance(strategy, RSIStrategy):
        # Calculate and show RSI
        rsi = calculate_rsi(data['close'], strategy.rsi_period)
        
        fig.add_trace(
            go.Scatter(x=data.index, y=rsi, name='RSI', line=dict(color='purple')),
            row=2, col=1
        )
        
        # Add RSI levels
        fig.add_hline(y=strategy.overbought, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=strategy.oversold, line_dash="dash", line_color="green", row=2, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)
    
    elif isinstance(strategy, BollingerBandsStrategy):
        # Calculate Bollinger Bands
        bb = calculate_bollinger_bands(data['close'], strategy.bb_period, strategy.bb_std)
        
        fig.add_trace(
            go.Scatter(x=data.index, y=bb['upper'], name='BB Upper', line=dict(color='red', dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=data.index, y=bb['middle'], name='BB Middle', line=dict(color='orange')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=data.index, y=bb['lower'], name='BB Lower', line=dict(color='green', dash='dash')),
            row=1, col=1
        )
        
        # Show band width
        band_width = (bb['upper'] - bb['lower']) / bb['middle'] * 100
        fig.add_trace(
            go.Scatter(x=data.index, y=band_width, name='Band Width %'),
            row=2, col=1
        )
    
    # Update layout
    fig.update_layout(
        title=f"{strategy_name} - {symbol} Analysis",
        xaxis_title="Date",
        height=600,
        showlegend=True
    )
    
    fig.update_xaxes(rangeslider_visible=False)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show latest signal
    if symbol in strategy.last_signals:
        signal = strategy.last_signals[symbol]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Latest Signal", signal.signal.value)
        with col2:
            st.metric("Confidence", f"{signal.confidence:.1%}")
        with col3:
            st.metric("Entry Price", f"₹{signal.entry_price:.2f}" if signal.entry_price else "N/A")
        with col4:
            st.metric("Stop Loss", f"₹{signal.stop_loss:.2f}" if signal.stop_loss else "N/A")


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict:
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    return {
        'upper': sma + (std * std_dev),
        'middle': sma,
        'lower': sma - (std * std_dev)
    }
