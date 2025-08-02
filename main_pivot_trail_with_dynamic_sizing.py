import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from tqdm import tqdm

# ==============================================================================
# DYNAMIC POSITION SIZING ADDITION
# ==============================================================================

def get_dynamic_risk_percentage(consecutive_losses):
    """
    Get risk percentage based on consecutive losses
    Trigger levels: 3,5,8,12,15,18+ with conservative step-down
    """
    if consecutive_losses < 3:
        return 0.020  # 2.0% base risk
    elif consecutive_losses < 5:
        return 0.016  # 1.6% after 3 losses
    elif consecutive_losses < 8:
        return 0.012  # 1.2% after 5 losses  
    elif consecutive_losses < 12:
        return 0.008  # 0.8% after 8 losses
    elif consecutive_losses < 15:
        return 0.004  # 0.4% after 12 losses
    elif consecutive_losses < 18:
        return 0.002  # 0.2% after 15 losses
    else:
        return 0.001  # 0.1% minimum after 18+ losses

# ==============================================================================
# ORIGINAL STRATEGY CODE (UNCHANGED)
# ==============================================================================

def load_data(csv_path):
    df = pd.read_csv(csv_path, parse_dates=['date'])
    df.sort_values('date', inplace=True)
    df.rename(columns={'date': 'datetime'}, inplace=True)  # Rename for consistency
    
    # Filter for regular market hours (9:15 AM to 3:30 PM)
    df['time'] = df['datetime'].dt.time
    market_start = pd.to_datetime('09:15').time()
    market_end = pd.to_datetime('15:30').time()
    df = df[(df['time'] >= market_start) & (df['time'] <= market_end)]
    df = df.drop('time', axis=1)
    
    return df

def calculate_pivots(df, leftBars=2, rightBars=2):
    pivots = []
    df_5min = df.resample('5min', on='datetime').agg({'high':'max', 'low':'min'})
    df_5min = df_5min.reset_index()
    for i in range(leftBars, len(df_5min)-rightBars):
        high = df_5min.loc[i, 'high']
        low = df_5min.loc[i, 'low']
        if high == max(df_5min.loc[i-leftBars:i+rightBars, 'high']):
            pivots.append({'type':'high', 'price':high, 'datetime':df_5min.loc[i, 'datetime']})
        if low == min(df_5min.loc[i-leftBars:i+rightBars, 'low']):
            pivots.append({'type':'low', 'price':low, 'datetime':df_5min.loc[i, 'datetime']})
    return pivots

def calculate_ema(series, period):
    """Calculate Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()

def calculate_options_position_size(capital, risk_percentage, sl_distance, entry_price):
    """
    Simple options position sizing with fixed assumptions
    
    Assumptions:
    - Option premium: ₹100 per contract (fixed)
    - Options leverage: 25x (for 1% futures move = 25% option move)
    - Position size based on capital and SL distance
    - Account for potential drawdown in sizing
    """
    risk_amount = capital * risk_percentage
    option_premium = 100  # Fixed ₹100 per option contract
    options_leverage = 25  # 1% futures move = 25% option move
    
    # Risk per option if SL is hit
    # Simple calculation: sl_distance with leverage factor
    risk_per_option = sl_distance * (options_leverage / 100)  # Convert leverage to decimal
    
    if risk_per_option <= 0:
        return 1
        
    # Position size to achieve target risk
    position_size = risk_amount / risk_per_option
    
    # Account for drawdown potential - reduce position size if capital is low
    drawdown_factor = max(0.5, capital / 100000)  # Reduce size if capital < 1L
    position_size *= drawdown_factor
    
    # Round to integer lots
    position_size = max(1, int(round(position_size)))
    
    # Cap position size to prevent over-leveraging
    max_position = capital / (option_premium * 2)  # Don't use more than 50% capital for premiums
    position_size = min(position_size, int(max_position))
    
    return max(1, position_size)

def calculate_1min_pivots(df, end_idx, start_idx=None, leftBars=5, rightBars=5, lookback_bars=100):
    """Calculate 1-minute pivots from a specific start point to end point"""
    if start_idx is None:
        start_idx = max(0, end_idx - lookback_bars)  # Default lookback
    
    # Get recent data for pivot calculation
    recent_data = df.iloc[start_idx:end_idx+1].copy()
    
    pivots = {'high_pivots': [], 'low_pivots': []}
    
    # Need at least leftBars + rightBars + 1 bars for pivot calculation
    min_bars_needed = leftBars + rightBars + 1
    if len(recent_data) < min_bars_needed:
        return pivots
    
    # Calculate pivot highs and lows
    for i in range(leftBars, len(recent_data) - rightBars):
        current_high = recent_data.iloc[i]['high']
        current_low = recent_data.iloc[i]['low']
        current_time = recent_data.iloc[i]['datetime']
        current_actual_idx = start_idx + i
        
        # Check for pivot high
        left_highs = recent_data.iloc[i-leftBars:i]['high'].values
        right_highs = recent_data.iloc[i+1:i+rightBars+1]['high'].values
        if len(left_highs) == leftBars and len(right_highs) == rightBars:
            if current_high >= max(left_highs) and current_high >= max(right_highs):
                pivots['high_pivots'].append({
                    'price': current_high,
                    'datetime': current_time,
                    'index': current_actual_idx
                })
        
        # Check for pivot low
        left_lows = recent_data.iloc[i-leftBars:i]['low'].values
        right_lows = recent_data.iloc[i+1:i+rightBars+1]['low'].values
        if len(left_lows) == leftBars and len(right_lows) == rightBars:
            if current_low <= min(left_lows) and current_low <= min(right_lows):
                pivots['low_pivots'].append({
                    'price': current_low,
                    'datetime': current_time,
                    'index': current_actual_idx
                })
    
    return pivots

def get_trailing_pivot_level(df, current_idx, direction, current_price, entry_idx):
    """Get the most recent relevant pivot for trailing from the entry point"""
    # Look at data from entry point to current bar
    # Look back a few more bars before entry to ensure we have enough data for 5,5 pivots
    start_idx = max(0, entry_idx - 10)  # Look back 10 bars from entry point
    end_idx = current_idx + 1
    
    # Calculate pivots only on the relevant data slice
    pivots = calculate_1min_pivots(df, end_idx, start_idx)
    
    if direction == 'long':
        # For long trades, use the highest pivot low that's below current price
        valid_lows = [p for p in pivots['low_pivots'] if p['price'] < current_price and p['index'] >= entry_idx]
        if valid_lows:
            # Return the most recent (highest index) pivot low
            return max(valid_lows, key=lambda x: x['index'])['price']
    else:  # short
        # For short trades, use the lowest pivot high that's above current price
        valid_highs = [p for p in pivots['high_pivots'] if p['price'] > current_price and p['index'] >= entry_idx]
        if valid_highs:
            # Return the most recent (highest index) pivot high
            return min(valid_highs, key=lambda x: x['index'])['price']
    
    return None

def backtest_strategy(df, pivots, detailed_log_count=3, validation_file="detailed_validation.txt"):
    trades = []
    open_trades = []  # Track open trades for intraday closure
    
    # Capital and risk management for options trading with DYNAMIC SIZING
    starting_capital = 100000  # 1 lakh starting capital
    current_capital = starting_capital
    base_risk_per_trade = 0.02  # 2% base risk per trade
    
    # DYNAMIC POSITION SIZING - Track consecutive losses
    consecutive_losses = 0
    last_trade_won = True  # Start with assumption of no previous loss
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # Setup detailed validation logging for first few trades
    validation_file = "trade_validation_log_pivot_trail_dynamic.txt"
    detailed_log_count = 5  # Number of trades to log in detail
    trades_logged = 0
    
    with open(validation_file, 'w') as val_file:
        val_file.write("=" * 80 + "\n")
        val_file.write("DETAILED TRADE VALIDATION LOG - FIRST 5 TRADES (PIVOT TRAIL WITH DYNAMIC SIZING)\n")
        val_file.write("=" * 80 + "\n")
        val_file.write("Purpose: Validate minute-by-minute strategy logic with 1-min pivot trail exit\n")
        val_file.write("Shows: Breakouts, marking candles, updates, entries, exits\n")
        val_file.write("DYNAMIC SIZING: Risk reduced based on consecutive losses\n")
        val_file.write("=" * 80 + "\n\n")
    
    # Convert pivots to a lookup by datetime for fast access
    pivot_highs = {p['datetime']: p['price'] for p in pivots if p['type'] == 'high'}
    pivot_lows = {p['datetime']: p['price'] for p in pivots if p['type'] == 'low'}
    
    logger.info(f"Starting pivot trail backtest with {len(pivot_highs)} pivot highs and {len(pivot_lows)} pivot lows")
    logger.info(f"DYNAMIC SIZING ENABLED - Base risk: {base_risk_per_trade*100:.1f}%, Min risk: 0.1%")
    
    # Group data by trading day for intraday management
    df['date'] = df['datetime'].dt.date
    trading_days = df['date'].unique()
    
    logger.info(f"Processing {len(trading_days)} trading days from {trading_days[0]} to {trading_days[-1]}")

    # Create validation file if detailed logging requested
    trades_logged = 0
    if detailed_log_count > 0:
        with open(validation_file, 'w') as val_file:
            val_file.write("5-MINUTE PIVOT BREAKOUT STRATEGY - DETAILED TRADE VALIDATION (PIVOT TRAIL EXIT WITH DYNAMIC SIZING)\n")
            val_file.write("="*80 + "\n")
            val_file.write("Strategy: 5-min pivot breakout with marking candle retracement entry\n")
            val_file.write("Parameters: 15,15 pivots, 5-bar marking window, 18-bar timeout, unlimited updates\n")
            val_file.write("Risk Management: Initial 1:2 RR, then 1-min pivot trail exit, 0.1% of entry SL limit\n")
            val_file.write("Exit Logic: Immediate 1-min pivot (5,5) trailing from entry vs original SL\n")
            val_file.write("Pivot Usage: Reusable - allows multiple breakout attempts until pivot updates\n")
            val_file.write("DYNAMIC SIZING: Risk reduces on consecutive losses, resets after 1 win\n")
            val_file.write("Dataset: NIFTY 1-min data with pivot trail exit validation logic\n")
            val_file.write("="*80 + "\n\n")
    
    # Iterate over 1-min bars with progress bar
    # Track state for marking candle logic (from validation script)
    marking_candle_active = False
    marking_direction = None
    marking_entry = 0
    marking_sl = 0
    marking_updates = 0
    marking_pivot = 0
    marking_pivot_time = None  # Store pivot time for marking as used after entry
    marking_breakout_idx = None  # Track breakout bar index for 5-bar window and 18-bar limit
    marking_breakout_high = 0  # Store breakout candle high for range validation
    marking_breakout_low = 0   # Store breakout candle low for range validation
    active_trade_info = None
    
    # Detailed logging state
    current_trade_bars = []  # Store bars for current trade setup
    
    def log_detailed_bar(i, row, dt, action=""):
        """Log detailed bar info for validation"""
        if len(current_trade_bars) > 0 or action.startswith("LONG BREAKOUT") or action.startswith("SHORT BREAKOUT"):
            bar_info = f"Bar {i+1:4d} | {dt.strftime('%H:%M')} | {row['open']:.1f}/{row['high']:.1f}/{row['low']:.1f}/{row['close']:.1f}"
            if marking_candle_active:
                # DYNAMIC SIZING: Show current risk level
                current_risk = get_dynamic_risk_percentage(consecutive_losses)
                bar_info += f" | Entry: {marking_entry:.1f} | SL: {marking_sl:.1f} | Risk: {current_risk*100:.1f}%"
            else:
                bar_info += " | Entry: - | SL: - | Risk: -"
            bar_info += f" | Close: {row['close']:.1f}"
            if action:
                bar_info += f" | {action}"
            current_trade_bars.append(bar_info)
    
    def write_trade_summary():
        """Write completed trade summary to validation file"""
        nonlocal trades_logged
        if trades_logged < detailed_log_count and current_trade_bars:
            with open(validation_file, 'a') as val_file:
                trades_logged += 1
                val_file.write(f"\n" + "="*80 + "\n")
                val_file.write(f"TRADE SETUP #{trades_logged} VALIDATION (PIVOT TRAIL WITH DYNAMIC SIZING)\n")
                val_file.write("="*80 + "\n")
                for bar_info in current_trade_bars:
                    val_file.write(bar_info + "\n")
                val_file.write("\n")
    
    # Create capital reference for passing to functions
    current_capital_ref = [current_capital]  # Use list for mutable reference
    
    for i in tqdm(range(len(df)), desc="Processing bars (Pivot Trail + Dynamic Sizing)", unit="bars"):
        row = df.iloc[i]
        dt = row['datetime']
        current_time = dt.time()
        current_date = dt.date()
        
        # Close all open trades at 15:25 (intraday rule)
        if current_time >= pd.to_datetime('15:25').time():
            if open_trades:
                logger.info(f"Closing {len(open_trades)} open trades at market close (15:25)")
                for trade_info in open_trades:
                    trade = close_trade_at_market_close(df, i, trade_info, current_capital_ref)
                    if trade:
                        trades.append(trade)
                        # DYNAMIC SIZING: Update consecutive losses based on trade result
                        if trade['pl_points'] > 0:
                            consecutive_losses = 0  # Reset on win
                            last_trade_won = True
                        else:
                            consecutive_losses += 1
                            last_trade_won = False
                        
                        logger.info(f"Trade #{len(trades)} closed at market close: {trade['direction']} P&L: {trade['pl_points']:.1f} | Consecutive losses: {consecutive_losses}")
                        # Update current capital from reference
                        current_capital = current_capital_ref[0]
                log_detailed_bar(i, row, dt, "MARKET CLOSE: All trades closed")
                open_trades = []
            # Also close any active marking candle setup
            if marking_candle_active:
                log_detailed_bar(i, row, dt, "MARKET CLOSE: Marking setup terminated")
                write_trade_summary()
                current_trade_bars = []
            marking_candle_active = False
            active_trade_info = None
            continue  # No new entries after 15:25
        
        # No new entries after 15:20 (5 minutes before close)
        if current_time >= pd.to_datetime('15:20').time():
            continue
            
        # Check for trade exits first (for open trades)
        remaining_trades = []
        for trade_info in open_trades:
            exit_result = check_trade_exit_pivot_trail(row, trade_info, df, i)
            if exit_result:
                trade = create_trade_result_from_exit(df, i, trade_info, exit_result, current_capital_ref)
                trades.append(trade)
                
                # DYNAMIC SIZING: Update consecutive losses based on trade result
                if trade['pl_points'] > 0:
                    consecutive_losses = 0  # Reset on win
                    last_trade_won = True
                    logger.info(f"WIN - Consecutive losses reset to 0")
                else:
                    consecutive_losses += 1
                    last_trade_won = False
                    logger.info(f"LOSS - Consecutive losses now: {consecutive_losses}")
                
                log_detailed_bar(i, row, dt, f"TRADE EXIT: {exit_result['type']} @ {exit_result['price']:.1f} | Consec losses: {consecutive_losses}")
                logger.info(f"Trade #{len(trades)} completed: {trade_info['direction']} {exit_result['type']} P&L: {trade['pl_points']:.1f}")
                
                # Update current capital from reference
                current_capital = current_capital_ref[0]
                if trades_logged < detailed_log_count:
                    write_trade_summary()
                    current_trade_bars = []
            else:
                # Update max favorable/adverse
                update_trade_excursions(row, trade_info)
                remaining_trades.append(trade_info)
        open_trades = remaining_trades
        
        # VALIDATION SCRIPT LOGIC - STEP 1: Check entry triggers FIRST (before any updates)
        if marking_candle_active and not active_trade_info:
            entry_triggered = False
            
            # DYNAMIC SIZING: Calculate current risk percentage
            current_risk_per_trade = get_dynamic_risk_percentage(consecutive_losses)
            
            if marking_direction == 'long':
                if row['high'] > marking_entry:  # HIGH > ENTRY (not >=)
                    logger.info(f"Entry triggered: long @ {marking_entry:.1f} | Risk: {current_risk_per_trade*100:.1f}% (Consec losses: {consecutive_losses})")
                    log_detailed_bar(i, row, dt, f"TRADE ENTRY: LONG @ {marking_entry:.1f} (High: {row['high']:.1f} > Entry) | Risk: {current_risk_per_trade*100:.1f}%")
                    # Calculate TP based on current SL distance (TP = Entry + 2 * SL_distance)
                    sl_distance = abs(marking_entry - marking_sl)
                    tp_price = marking_entry + 2 * sl_distance
                    
                    # Calculate position size for options trading with DYNAMIC RISK
                    position_size = calculate_options_position_size(
                        current_capital, current_risk_per_trade, sl_distance, marking_entry
                    )
                    
                    # Create trade info for tracking
                    active_trade_info = {
                        'direction': 'long',
                        'entry_price': marking_entry,
                        'sl_price': marking_sl,
                        'tp_price': tp_price,
                        'entry_time': dt,
                        'entry_idx': i,
                        'updates': marking_updates,
                        'entered': True,
                        'max_favorable': 0,
                        'max_adverse': 0,
                        'pivot_level': marking_pivot,
                        'breakout_time': dt,  # Use entry time as placeholder
                        'trailing_stop': None,  # Track pivot trailing stop level
                        'position_size': position_size,  # Track options position size
                        'entry_capital': current_capital,  # Track capital at entry
                        'risk_percentage': current_risk_per_trade,  # Track risk used
                        'consecutive_losses_at_entry': consecutive_losses  # Track loss streak at entry
                    }
                    open_trades.append(active_trade_info)
                    # Pivot can be reused for future breakouts - no marking as used
                    entry_triggered = True
                    
            elif marking_direction == 'short':
                if row['low'] < marking_entry:  # LOW < ENTRY (not <=)
                    logger.info(f"Entry triggered: short @ {marking_entry:.1f} | Risk: {current_risk_per_trade*100:.1f}% (Consec losses: {consecutive_losses})")
                    log_detailed_bar(i, row, dt, f"TRADE ENTRY: SHORT @ {marking_entry:.1f} (Low: {row['low']:.1f} < Entry) | Risk: {current_risk_per_trade*100:.1f}%")
                    # Calculate TP based on current SL distance (TP = Entry - 2 * SL_distance)
                    sl_distance = abs(marking_sl - marking_entry)
                    tp_price = marking_entry - 2 * sl_distance
                    
                    # Calculate position size for options trading with DYNAMIC RISK
                    position_size = calculate_options_position_size(
                        current_capital, current_risk_per_trade, sl_distance, marking_entry
                    )
                    
                    # Create trade info for tracking
                    active_trade_info = {
                        'direction': 'short',
                        'entry_price': marking_entry,
                        'sl_price': marking_sl,
                        'tp_price': tp_price,
                        'entry_time': dt,
                        'entry_idx': i,
                        'updates': marking_updates,
                        'entered': True,
                        'max_favorable': 0,
                        'max_adverse': 0,
                        'pivot_level': marking_pivot,
                        'breakout_time': dt,  # Use entry time as placeholder
                        'trailing_stop': None,  # Track pivot trailing stop level
                        'position_size': position_size,  # Track options position size
                        'entry_capital': current_capital,  # Track capital at entry
                        'risk_percentage': current_risk_per_trade,  # Track risk used
                        'consecutive_losses_at_entry': consecutive_losses  # Track loss streak at entry
                    }
                    open_trades.append(active_trade_info)
                    # Pivot can be reused for future breakouts - no marking as used
                    entry_triggered = True
            
            # If entry triggered, stop processing this bar for marking candle
            if entry_triggered:
                marking_candle_active = False
                marking_breakout_idx = None  # Reset breakout tracking
                # Don't write trade summary yet - wait for exit
                continue
        
        # Find latest pivot high/low before current bar
        pivot_high = None
        pivot_high_time = None
        pivot_low = None
        pivot_low_time = None
        
        for pdt in sorted(pivot_highs.keys()):
            if pdt < dt:
                pivot_high = pivot_highs[pdt]
                pivot_high_time = pdt
            else:
                break
        for pdt in sorted(pivot_lows.keys()):
            if pdt < dt:
                pivot_low = pivot_lows[pdt]
                pivot_low_time = pdt
            else:
                break
        
        # VALIDATION SCRIPT LOGIC - STEP 2: Check for breakouts (only if no active trade)
        if not active_trade_info and not marking_candle_active:
            # Check for breakout (long) - pivots can be reused for multiple attempts
            if (pivot_high and row['high'] > pivot_high and row['close'] > row['open']):
                logger.info(f"Long breakout detected at {dt} - Pivot: {pivot_high:.1f}, High: {row['high']:.1f}")
                log_detailed_bar(i, row, dt, f"LONG BREAKOUT: Pivot {pivot_high:.1f} broken, High: {row['high']:.1f}")
                # Set up marking direction
                marking_direction = 'long'
                marking_pivot = pivot_high
                marking_pivot_time = pivot_high_time  # Store pivot time for reference
                marking_breakout_idx = i  # Store breakout bar index for windows
                marking_breakout_high = row['high']  # Store breakout range
                marking_breakout_low = row['low']    # Store breakout range
                # Pivots can be reused - allow multiple breakout attempts
                
            # Check for breakout (short) - pivots can be reused for multiple attempts
            elif (pivot_low and row['low'] < pivot_low and row['close'] < row['open']):
                logger.info(f"Short breakout detected at {dt} - Pivot: {pivot_low:.1f}, Low: {row['low']:.1f}")
                log_detailed_bar(i, row, dt, f"SHORT BREAKOUT: Pivot {pivot_low:.1f} broken, Low: {row['low']:.1f}")
                # Set up marking direction
                marking_direction = 'short'
                marking_pivot = pivot_low
                marking_pivot_time = pivot_low_time  # Store pivot time for reference
                marking_breakout_idx = i  # Store breakout bar index for windows
                marking_breakout_high = row['high']  # Store breakout range
                marking_breakout_low = row['low']    # Store breakout range
                # Pivots can be reused - allow multiple breakout attempts
        
        # VALIDATION SCRIPT LOGIC - STEP 3: Check for marking candle pattern (within 5 bars of breakout)
        if marking_direction and not marking_candle_active and not active_trade_info and marking_breakout_idx is not None:
            bars_since_breakout = i - marking_breakout_idx
            
            # Only search for marking candle within NEXT 5 bars after breakout (not same bar)
            if 1 <= bars_since_breakout <= 5:
                if marking_direction == 'long' and row['close'] < row['open']:  # RED candle for LONG
                    # Check if close is within breakout candle range
                    if marking_breakout_low <= row['close'] <= marking_breakout_high:
                        logger.info(f"Marking candle found for LONG trade (bar {bars_since_breakout} after breakout)")
                        log_detailed_bar(i, row, dt, f"MARKING CANDLE FOUND (LONG): Red candle, close in range [{marking_breakout_low:.1f}-{marking_breakout_high:.1f}]")
                        marking_entry = row['high'] + 0.1  # Add 0.1 buffer for proper cross, not just touch
                        marking_sl = row['low']
                        
                        # Check max SL distance (0.1% of entry price limit)
                        sl_distance = abs(marking_entry - marking_sl)
                        max_sl_distance = marking_entry * 0.001  # 0.1% of entry price
                        if sl_distance <= max_sl_distance:
                            marking_candle_active = True
                            marking_updates = 0
                            # DYNAMIC SIZING: Show current risk in log
                            current_risk = get_dynamic_risk_percentage(consecutive_losses)
                            log_detailed_bar(i, row, dt, f"SETUP ACTIVATED: Entry {marking_entry:.1f}, SL {marking_sl:.1f} (distance: {sl_distance:.1f}, max: {max_sl_distance:.1f}) Risk: {current_risk*100:.1f}%")
                            logger.info(f"Long trade setup pending entry - Entry: {marking_entry:.1f}, SL: {marking_sl:.1f}, Risk: {current_risk*100:.1f}%")
                        else:
                            logger.info(f"Trade skipped - SL distance {sl_distance:.1f} exceeds 0.1% of entry ({max_sl_distance:.1f})")
                            log_detailed_bar(i, row, dt, f"SETUP REJECTED: SL distance {sl_distance:.1f} > 0.1% of entry ({max_sl_distance:.1f})")
                            write_trade_summary()
                            current_trade_bars = []
                            marking_direction = None
                            marking_breakout_idx = None
                    else:
                        logger.info(f"Red candle found but close {row['close']:.1f} not in breakout range [{marking_breakout_low:.1f}-{marking_breakout_high:.1f}]")
                        log_detailed_bar(i, row, dt, f"RED CANDLE: Close {row['close']:.1f} outside breakout range [{marking_breakout_low:.1f}-{marking_breakout_high:.1f}]")
                    
                elif marking_direction == 'short' and row['close'] > row['open']:  # GREEN candle for SHORT
                    # Check if close is within breakout candle range
                    if marking_breakout_low <= row['close'] <= marking_breakout_high:
                        logger.info(f"Marking candle found for SHORT trade (bar {bars_since_breakout} after breakout)")
                        log_detailed_bar(i, row, dt, f"MARKING CANDLE FOUND (SHORT): Green candle, close in range [{marking_breakout_low:.1f}-{marking_breakout_high:.1f}]")
                        marking_entry = row['low'] - 0.1  # Subtract 0.1 buffer for proper cross, not just touch
                        marking_sl = row['high']
                        
                        # Check max SL distance (0.1% of entry price limit)
                        sl_distance = abs(marking_sl - marking_entry)
                        max_sl_distance = marking_entry * 0.001  # 0.1% of entry price
                        if sl_distance <= max_sl_distance:
                            marking_candle_active = True
                            marking_updates = 0
                            # DYNAMIC SIZING: Show current risk in log
                            current_risk = get_dynamic_risk_percentage(consecutive_losses)
                            log_detailed_bar(i, row, dt, f"SETUP ACTIVATED: Entry {marking_entry:.1f}, SL {marking_sl:.1f} (distance: {sl_distance:.1f}, max: {max_sl_distance:.1f}) Risk: {current_risk*100:.1f}%")
                            logger.info(f"Short trade setup pending entry - Entry: {marking_entry:.1f}, SL: {marking_sl:.1f}, Risk: {current_risk*100:.1f}%")
                        else:
                            logger.info(f"Trade skipped - SL distance {sl_distance:.1f} exceeds 0.1% of entry ({max_sl_distance:.1f})")
                            marking_direction = None
                            marking_breakout_idx = None
                    else:
                        logger.info(f"Green candle found but close {row['close']:.1f} not in breakout range [{marking_breakout_low:.1f}-{marking_breakout_high:.1f}]")
            elif bars_since_breakout > 5:
                # No marking candle found within 5 bars, reset and wait for next breakout
                logger.info(f"No marking candle found within 5 bars after breakout, resetting setup")
                log_detailed_bar(i, row, dt, "5-BAR TIMEOUT: No marking candle found, setup expired")
                write_trade_summary()
                current_trade_bars = []
                marking_direction = None
                marking_breakout_idx = None
        
        # VALIDATION SCRIPT LOGIC - STEP 4: Update marking levels (only if no entry triggered this bar)
        elif marking_candle_active and not active_trade_info and marking_breakout_idx is not None:
            bars_from_breakout = i - marking_breakout_idx
            
            # Check if we've exceeded the 3-update limit
            if marking_updates >= 3:
                logger.info(f"Maximum 3 marking candle updates reached, ignoring trade setup")
                log_detailed_bar(i, row, dt, "MAX UPDATES REACHED: Trade setup ignored (>3 updates)")
                write_trade_summary()
                current_trade_bars = []
                marking_candle_active = False
                marking_direction = None
                marking_breakout_idx = None
            # Only allow updates within 18 bars from breakout AND max 3 updates
            elif bars_from_breakout <= 18 and marking_updates < 3:
                old_entry = marking_entry
                old_sl = marking_sl
                
                if marking_direction == 'long':
                    # Check if SL needs to be extended (low goes below current SL)
                    if row['low'] < marking_sl:
                        new_entry = row['high'] + 0.1  # Add 0.1 buffer for proper cross
                        new_sl = row['low']
                        new_sl_distance = abs(new_entry - new_sl)
                        max_sl_distance = new_entry * 0.001  # 0.1% of entry price
                        
                        if new_sl_distance <= max_sl_distance:  # Check 0.1% limit
                            marking_entry = new_entry
                            marking_sl = new_sl
                            marking_updates += 1
                            candle_color = "Red" if row['close'] < row['open'] else "Green"
                            log_detailed_bar(i, row, dt, f"MARKING UPDATE #{marking_updates} (LONG {candle_color}): Entry {old_entry:.1f}→{marking_entry:.1f}, SL {old_sl:.1f}→{marking_sl:.1f}")
                            logger.info(f"Marking candle updated (Long {candle_color}) - Old Entry: {old_entry:.1f}, New Entry: {marking_entry:.1f}, Old SL: {old_sl:.1f}, New SL: {marking_sl:.1f}")
                        
                elif marking_direction == 'short':
                    # Check if SL needs to be extended (high goes above current SL)
                    if row['high'] > marking_sl:
                        new_entry = row['low'] - 0.1  # Subtract 0.1 buffer for proper cross
                        new_sl = row['high']
                        new_sl_distance = abs(new_sl - new_entry)
                        max_sl_distance = new_entry * 0.001  # 0.1% of entry price
                        
                        if new_sl_distance <= max_sl_distance:  # Check 0.1% limit
                            marking_entry = new_entry
                            marking_sl = new_sl
                            marking_updates += 1
                            candle_color = "Red" if row['close'] < row['open'] else "Green"
                            log_detailed_bar(i, row, dt, f"MARKING UPDATE #{marking_updates} (SHORT {candle_color}): Entry {old_entry:.1f}→{marking_entry:.1f}, SL {old_sl:.1f}→{marking_sl:.1f}")
                            logger.info(f"Marking candle updated (Short {candle_color}) - Old Entry: {old_entry:.1f}, New Entry: {marking_entry:.1f}, Old SL: {old_sl:.1f}, New SL: {marking_sl:.1f}")
            else:
                # 18-bar limit reached, expire the marking setup
                logger.info(f"18-bar limit reached from breakout, expiring marking setup")
                log_detailed_bar(i, row, dt, "18-BAR TIMEOUT: Marking setup expired")
                write_trade_summary()
                current_trade_bars = []
                marking_candle_active = False
                marking_direction = None
                marking_breakout_idx = None
                
    # Close any remaining open trades at end of backtest
    if open_trades:
        logger.info(f"Closing {len(open_trades)} remaining open trades at end of backtest")
        for trade_info in open_trades:
            if trade_info['entered']:
                trade = close_trade_at_market_close(df, len(df)-1, trade_info, current_capital_ref)
                if trade:
                    trades.append(trade)
                    # DYNAMIC SIZING: Update consecutive losses for final trades
                    if trade['pl_points'] > 0:
                        consecutive_losses = 0
                    else:
                        consecutive_losses += 1
                    
    logger.info(f"Pivot Trail Backtest completed. Total trades: {len(trades)}")
    logger.info(f"Final capital: ₹{current_capital_ref[0]:,.2f} (Started with ₹{starting_capital:,})")
    logger.info(f"Final consecutive losses: {consecutive_losses}")
    return trades

def update_trade_excursions(row, trade_info):
    """Update max favorable and adverse excursions for entered trades"""
    if not trade_info['entered']:
        return
        
    entry_price = trade_info['entry_price']
    direction = trade_info['direction']
    
    if direction == 'long':
        current_pl = row['high'] - entry_price  # Best case
        current_adverse = entry_price - row['low']  # Worst case
    else:
        current_pl = entry_price - row['low']  # Best case
        current_adverse = row['high'] - entry_price  # Worst case
    
    trade_info['max_favorable'] = max(trade_info['max_favorable'], current_pl)
    trade_info['max_adverse'] = max(trade_info['max_adverse'], current_adverse)

def check_trade_exit_pivot_trail(row, trade_info, df, current_idx):
    """Check if trade should exit using immediate 1-minute pivot trailing"""
    if not trade_info['entered']:
        return None
        
    direction = trade_info['direction']
    sl_price = trade_info['sl_price']
    entry_price = trade_info['entry_price']
    current_price = row['close']
    
    # Get current 1-minute pivot level for trailing
    trailing_level = get_trailing_pivot_level(df, current_idx, direction, current_price, trade_info['entry_idx'])
    
    if direction == 'long':
        # Determine which stop to use: pivot or original SL
        if trailing_level is not None:
            # Use pivot if it's closer to current price than original SL
            distance_to_pivot = current_price - trailing_level
            distance_to_sl = current_price - sl_price
            
            if distance_to_pivot < distance_to_sl and trailing_level > sl_price:
                # Pivot is closer and higher than original SL - use pivot trailing
                if 'trailing_stop' not in trade_info or trade_info['trailing_stop'] is None or trailing_level > trade_info['trailing_stop']:
                    trade_info['trailing_stop'] = trailing_level
                
                # Check if price hits the pivot trailing stop
                if row['low'] <= trade_info['trailing_stop']:
                    return {'type': 'PIVOT_TRAIL', 'price': trade_info['trailing_stop']}
            else:
                # Use original SL if pivot is farther or lower
                if row['low'] <= sl_price:
                    return {'type': 'SL', 'price': sl_price}
        else:
            # No pivot available, use original SL
            if row['low'] <= sl_price:
                return {'type': 'SL', 'price': sl_price}
            
    else:  # short
        # Determine which stop to use: pivot or original SL
        if trailing_level is not None:
            # Use pivot if it's closer to current price than original SL
            distance_to_pivot = trailing_level - current_price
            distance_to_sl = sl_price - current_price
            
            if distance_to_pivot < distance_to_sl and trailing_level < sl_price:
                # Pivot is closer and lower than original SL - use pivot trailing
                if trade_info['trailing_stop'] is None or trailing_level < trade_info['trailing_stop']:
                    trade_info['trailing_stop'] = trailing_level
                
                # Check if price hits the pivot trailing stop
                if row['high'] >= trade_info['trailing_stop']:
                    return {'type': 'PIVOT_TRAIL', 'price': trade_info['trailing_stop']}
            else:
                # Use original SL if pivot is farther or higher
                if row['high'] >= sl_price:
                    return {'type': 'SL', 'price': sl_price}
        else:
            # No pivot available, use original SL
            if row['high'] >= sl_price:
                return {'type': 'SL', 'price': sl_price}
    
    return None

def create_trade_result_from_exit(df, exit_idx, trade_info, exit_result, current_capital_ref):
    """Create final trade result when exit is triggered"""
    entry_time = trade_info['entry_time']
    exit_time = df.iloc[exit_idx]['datetime']
    time_in_trade = exit_time - entry_time
    
    entry_price = trade_info['entry_price']
    exit_price = exit_result['price']
    position_size = trade_info.get('position_size', 1)  # Use calculated position size
    
    # Simple options P&L calculation with 25x leverage
    # 
    # Assumptions:
    # - Option premium: ₹100 per contract
    # - 1% futures move = 25% option move
    # - Simple multiplier approach
    #
    # Example: 100 point futures move = 1% on NIFTY 10,000
    # - Option move: 25% of ₹100 = ₹25 gain per contract
    # - Position size: Based on risk management
    # - Total P&L: position_size × option_gain
    
    options_leverage = 25  # 25x leverage factor
    option_premium = 100   # Fixed ₹100 per contract
    
    # Calculate P&L in points (futures price movement)
    if trade_info['direction'] == 'long':
        pl_points = (exit_price - entry_price)
    else:
        pl_points = (entry_price - exit_price)
    
    # Convert futures move to option premium change
    # 1% futures move (100 points on 10,000) = 25% option move (₹25 on ₹100)
    futures_move_percent = pl_points / entry_price  # Convert points to percentage
    option_move_percent = futures_move_percent * options_leverage  # Apply leverage
    option_premium_change = option_premium * option_move_percent  # Change in premium
    
    # Total P&L = position_size × option_premium_change
    actual_pl = position_size * option_premium_change
    
    # Update capital
    current_capital_ref[0] += actual_pl
    current_capital_ref[0] = max(current_capital_ref[0], 1000)  # Minimum capital floor
    
    sl_distance = abs(entry_price - trade_info['sl_price'])
    
    return {
        'trade_num': None,  # Will be set later
        'breakout_time': trade_info['breakout_time'],
        'entry_time': entry_time,
        'exit_time': exit_time,
        'direction': trade_info['direction'],
        'pivot_level': trade_info['pivot_level'],
        'entry_price': entry_price,
        'sl_price': trade_info['sl_price'],
        'tp_price': trade_info['tp_price'],
        'exit_price': exit_price,
        'result': exit_result['type'],
        'pl_points': pl_points,
        'sl_distance': sl_distance,
        'rr_achieved': pl_points / sl_distance if sl_distance > 0 else 0,
        'max_favorable': trade_info['max_favorable'],
        'max_adverse': trade_info['max_adverse'],
        'max_rr_potential': trade_info['max_favorable'] / sl_distance if sl_distance > 0 else 0,
        'time_in_trade_minutes': time_in_trade.total_seconds() / 60,
        'marking_updates': trade_info['updates'],
        'exit_size': position_size,  # Track actual position size
        'rr_target_achieved': trade_info.get('rr_achieved', False),  # Track if 1:2 was reached
        'actual_pl': actual_pl,  # Track actual P&L in rupees
        'entry_capital': trade_info['entry_capital'],  # Track capital at entry
        'exit_capital': current_capital_ref[0],  # Track capital after exit
        'risk_percentage': trade_info.get('risk_percentage', 0.02),  # Track risk used
        'consecutive_losses_at_entry': trade_info.get('consecutive_losses_at_entry', 0)  # Track loss streak
    }

def close_trade_at_market_close(df, close_idx, trade_info, current_capital_ref):
    """Close trade at market close (15:25)"""
    if not trade_info['entered']:
        return None  # Can't close a trade that never entered
        
    close_row = df.iloc[close_idx]
    close_price = close_row['close']  # Use closing price
    
    # Create exit result for market close
    exit_result = {'type': 'CLOSE', 'price': close_price}
    
    return create_trade_result_from_exit(df, close_idx, trade_info, exit_result, current_capital_ref)

def calculate_analytics(trades, df):
    if not trades:
        return {"message": "No trades to analyze"}
    
    # Basic trade statistics
    total_trades = len(trades)
    wins = sum(1 for t in trades if t['pl_points'] > 0)
    losses = total_trades - wins
    win_rate = wins / total_trades * 100
    
    # P&L statistics
    total_pl = sum(t['pl_points'] for t in trades)
    winning_trades = [t for t in trades if t['pl_points'] > 0]
    losing_trades = [t for t in trades if t['pl_points'] <= 0]
    
    avg_win = np.mean([t['pl_points'] for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t['pl_points'] for t in losing_trades]) if losing_trades else 0
    profit_factor = (wins * avg_win) / abs(losses * avg_loss) if losses > 0 and avg_loss != 0 else float('inf')
    
    # Risk-reward statistics
    avg_rr = np.mean([t['rr_achieved'] for t in trades])
    max_rr = max([t['rr_achieved'] for t in trades])
    min_rr = min([t['rr_achieved'] for t in trades])
    
    # Pivot Trail-specific statistics
    pivot_trail_exits = sum(1 for t in trades if t['result'] == 'PIVOT_TRAIL')
    sl_exits = sum(1 for t in trades if t['result'] == 'SL')
    close_exits = sum(1 for t in trades if t['result'] == 'CLOSE')
    rr_target_achieved = sum(1 for t in trades if t.get('rr_target_achieved', False))
    
    # Dynamic sizing statistics
    risk_levels_used = [t.get('risk_percentage', 0.02) for t in trades]
    avg_risk_used = np.mean(risk_levels_used) * 100
    min_risk_used = min(risk_levels_used) * 100
    max_risk_used = max(risk_levels_used) * 100
    
    # Count trades at each risk level
    risk_counts = {}
    for risk in risk_levels_used:
        risk_pct = risk * 100
        if risk_pct in risk_counts:
            risk_counts[risk_pct] += 1
        else:
            risk_counts[risk_pct] = 1
    
    # Drawdown and streak analysis
    cumulative_pl = np.cumsum([t['pl_points'] for t in trades])
    peak = np.maximum.accumulate(cumulative_pl)
    drawdown = peak - cumulative_pl
    max_drawdown = np.max(drawdown)
    
    # Win/loss streaks
    results = [1 if t['pl_points'] > 0 else -1 for t in trades]
    streaks = []
    current_streak = 1
    for i in range(1, len(results)):
        if results[i] == results[i-1]:
            current_streak += 1
        else:
            streaks.append(current_streak * results[i-1])
            current_streak = 1
    streaks.append(current_streak * results[-1])
    
    max_win_streak = max([s for s in streaks if s > 0]) if any(s > 0 for s in streaks) else 0
    max_loss_streak = abs(min([s for s in streaks if s < 0])) if any(s < 0 for s in streaks) else 0
    
    # Time-based analysis
    first_trade = min(trades, key=lambda t: t['entry_time'])
    last_trade = max(trades, key=lambda t: t['exit_time'])
    total_days = (last_trade['exit_time'] - first_trade['exit_time']).days
    
    # CAGR calculation using actual capital tracking from trades
    if trades:
        # Use actual capital tracking from trade execution
        initial_capital = trades[0]['entry_capital'] if trades else 100000
        final_capital = trades[-1]['exit_capital'] if trades else initial_capital
        
        if total_days > 0 and final_capital > 0:
            cagr = ((final_capital / initial_capital) ** (365.25 / total_days) - 1) * 100
        else:
            cagr = 0
    else:
        cagr = 0
        initial_capital = 100000
        final_capital = 100000
    
    # Directional analysis
    long_trades = [t for t in trades if t['direction'] == 'long']
    short_trades = [t for t in trades if t['direction'] == 'short']
    
    analytics = {
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'win_rate': round(win_rate, 2),
        'total_pl_points': round(total_pl, 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'profit_factor': round(profit_factor, 2),
        'avg_rr': round(avg_rr, 2),
        'max_rr': round(max_rr, 2),
        'min_rr': round(min_rr, 2),
        'max_drawdown': round(max_drawdown, 2),
        'max_win_streak': max_win_streak,
        'max_loss_streak': max_loss_streak,
        'cagr': round(cagr, 2),
        'total_days': total_days,
        'initial_capital': initial_capital,
        'final_capital': round(final_capital, 2),
        'total_return': round((final_capital - initial_capital) / initial_capital * 100, 2),
        'total_pl_rupees': round(final_capital - initial_capital, 2),  # Actual P&L in rupees
        'avg_position_size': round(np.mean([t.get('exit_size', 1) for t in trades]), 2),  # Average position size
        'avg_risk_used': round(avg_risk_used, 1),  # Average risk percentage used
        'min_risk_used': round(min_risk_used, 1),  # Minimum risk used
        'max_risk_used': round(max_risk_used, 1),  # Maximum risk used
        'risk_distribution': risk_counts,  # Distribution of risk levels
        'capital_efficiency': round(final_capital / initial_capital, 2),  # Multiple of initial capital
        'long_trades': len(long_trades),
        'short_trades': len(short_trades),
        'long_win_rate': round(sum(1 for t in long_trades if t['pl_points'] > 0) / len(long_trades) * 100, 2) if long_trades else 0,
        'short_win_rate': round(sum(1 for t in short_trades if t['pl_points'] > 0) / len(short_trades) * 100, 2) if short_trades else 0,
        'avg_time_in_trade': round(np.mean([t['time_in_trade_minutes'] for t in trades]), 2),
        'max_favorable_avg': round(np.mean([t['max_favorable'] for t in trades]), 2),
        'max_adverse_avg': round(np.mean([t['max_adverse'] for t in trades]), 2),
        'pivot_trail_exits': pivot_trail_exits,
        'sl_exits': sl_exits,
        'close_exits': close_exits,
        'rr_target_achieved': rr_target_achieved,
        'rr_achievement_rate': round(rr_target_achieved / total_trades * 100, 2) if total_trades > 0 else 0
    }
    
    return analytics

def print_analytics(analytics):
    print("\n" + "="*70)
    print("BACKTEST ANALYTICS SUMMARY (PIVOT TRAIL WITH DYNAMIC SIZING)")
    print("="*70)
    
    print(f"Total Trades: {analytics['total_trades']}")
    print(f"Wins: {analytics['wins']} | Losses: {analytics['losses']}")
    print(f"Win Rate: {analytics['win_rate']}%")
    print(f"Total P&L: {analytics['total_pl_points']} points")
    print(f"Average Win: {analytics['avg_win']} points")
    print(f"Average Loss: {analytics['avg_loss']} points")
    print(f"Profit Factor: {analytics['profit_factor']}")
    print(f"Initial Capital: ₹{analytics['initial_capital']:,}")
    print(f"Final Capital: ₹{analytics['final_capital']:,.2f}")
    print(f"Total Return: {analytics['total_return']}%")
    print(f"Capital Efficiency: {analytics['capital_efficiency']}x")
    print(f"CAGR: {analytics['cagr']}%")
    print(f"Max Drawdown: {analytics['max_drawdown']} points")
    print(f"Max Win Streak: {analytics['max_win_streak']}")
    print(f"Max Loss Streak: {analytics['max_loss_streak']}")
    print(f"Average R:R: {analytics['avg_rr']}")
    print(f"Max R:R Achieved: {analytics['max_rr']}")
    print(f"Min R:R Achieved: {analytics['min_rr']}")
    print("\n" + "="*50)
    print("DYNAMIC POSITION SIZING ANALYTICS:")
    print("="*50)
    print(f"Average Risk Used: {analytics['avg_risk_used']}%")
    print(f"Risk Range: {analytics['min_risk_used']}% - {analytics['max_risk_used']}%")
    print("Risk Distribution:")
    for risk_pct, count in sorted(analytics['risk_distribution'].items()):
        percentage = (count / analytics['total_trades']) * 100
        print(f"  {risk_pct:.1f}% risk: {count} trades ({percentage:.1f}%)")
    print("\n" + "="*50)
    print("EXIT TYPE BREAKDOWN:")
    print("="*50)
    print(f"Pivot Trail Exits: {analytics['pivot_trail_exits']}")
    print(f"Stop Loss Exits: {analytics['sl_exits']}")
    print(f"Market Close Exits: {analytics['close_exits']}")
    print(f"1:2 Target Achieved: {analytics['rr_target_achieved']} ({analytics['rr_achievement_rate']}%)")
    print("="*50)
    print(f"Long Trades: {analytics['long_trades']} (Win Rate: {analytics['long_win_rate']}%)")
    print(f"Short Trades: {analytics['short_trades']} (Win Rate: {analytics['short_win_rate']}%)")
    print(f"Avg Time in Trade: {analytics['avg_time_in_trade']} minutes")
    print(f"Avg Max Favorable: {analytics['max_favorable_avg']} points")
    print(f"Avg Max Adverse: {analytics['max_adverse_avg']} points")
    print(f"Backtest Period: {analytics['total_days']} days")

def print_trade_details(trades):
    print("\n" + "="*120)
    print("DETAILED TRADE ANALYSIS (PIVOT TRAIL WITH DYNAMIC SIZING)")
    print("="*120)
    
    headers = ['Trade#', 'Date', 'Dir', 'Entry', 'SL', 'TP', 'Exit', 'Result', 'P&L', 'R:R', 'Risk%', 'Size', 'Time(min)', '1:2?']
    print(f"{headers[0]:<6} {headers[1]:<12} {headers[2]:<5} {headers[3]:<8} {headers[4]:<8} {headers[5]:<8} {headers[6]:<8} {headers[7]:<6} {headers[8]:<8} {headers[9]:<6} {headers[10]:<6} {headers[11]:<6} {headers[12]:<10} {headers[13]:<5}")
    print("-" * 120)
    
    for i, trade in enumerate(trades, 1):
        trade['trade_num'] = i
        date_str = trade['entry_time'].strftime('%Y-%m-%d')
        rr_achieved = 'Yes' if trade.get('rr_target_achieved', False) else 'No'
        risk_pct = trade.get('risk_percentage', 0.02) * 100
        size = trade.get('exit_size', 1)
        print(f"{i:<6} {date_str:<12} {trade['direction'][:4]:<5} {trade['entry_price']:<8.1f} {trade['sl_price']:<8.1f} {trade['tp_price']:<8.1f} {trade['exit_price']:<8.1f} {trade['result']:<6} {trade['pl_points']:<8.1f} {trade['rr_achieved']:<6.2f} {risk_pct:<6.1f} {size:<6} {trade['time_in_trade_minutes']:<10.0f} {rr_achieved:<5}")

def main():
    csv_path = 'NIFTY 50_minute_data.csv'
    print("="*70)
    print("5-MINUTE PIVOT BREAKOUT STRATEGY BACKTEST (PIVOT TRAIL WITH DYNAMIC SIZING)")
    print("="*70)
    print("Strategy Parameters:")
    print("- Pivots: 15,15 on 5-min candles")
    print("- Market Hours: 9:15 AM - 3:30 PM only")
    print("- Intraday Trading: No entries after 15:20, Close all at 15:25")
    print("- Max SL Distance: 0.1% of entry price")
    print("- Reusable pivots (multiple breakout attempts allowed)")
    print("- 18-bar limit from breakout candle")
    print("- Unlimited marking candle updates within 18-bar window")
    print("- SL extension trigger: Any SL extension (not SL-1)")
    print("- EXIT LOGIC: Immediate 1-min pivot (5,5) trailing from entry vs original SL")
    print("- 1-min pivot calculation: 5 left bars, 5 right bars from entry point")
    print("- Trailing logic: Use pivot if closer to price than original SL")
    print("- Max marking updates: 3 (trade ignored if exceeded)")
    print("- DYNAMIC SIZING: Risk reduces based on consecutive losses")
    print("  * Base Risk: 2.0%, reduces at 3,5,8,12,15,18+ losses")
    print("  * Minimum Risk: 0.1%, resets after 1 win")
    print("="*70)
    
    print("Loading data...")
    df = load_data(csv_path)
    print(f"Loaded {len(df)} rows from {df['datetime'].min()} to {df['datetime'].max()}")
    
    # Check market session hours
    sample_times = df['datetime'].dt.time
    print(f"Market session: {sample_times.min()} to {sample_times.max()}")
    
    print("Calculating pivots...")
    pivots = calculate_pivots(df, leftBars=15, rightBars=15)  # Updated to 15,15
    print(f"Found {len(pivots)} pivots")
    
    print("Running backtest with dynamic position sizing and progress tracking...")
    trades = backtest_strategy(df, pivots)
    
    if trades:
        print_trade_details(trades)
        analytics = calculate_analytics(trades, df)
        print_analytics(analytics)
        
        # Export to CSV with additional analytics
        trades_df = pd.DataFrame(trades)
        trades_df.to_csv('backtest_results_pivot_trail_dynamic.csv', index=False)
        
        print(f"\nTrade details exported to 'backtest_results_pivot_trail_dynamic.csv'")
        print(f"Detailed logs available in the console output above")
        
        # Summary of dynamic sizing impact
        print(f"\n{'='*70}")
        print("DYNAMIC SIZING IMPACT SUMMARY")
        print(f"{'='*70}")
        print(f"Risk Distribution:")
        for risk_pct, count in sorted(analytics['risk_distribution'].items()):
            percentage = (count / analytics['total_trades']) * 100
            print(f"  {risk_pct:.1f}% risk: {count:4d} trades ({percentage:5.1f}%)")
        print(f"Average Risk Used: {analytics['avg_risk_used']:5.1f}%")
        print(f"Risk Range: {analytics['min_risk_used']:5.1f}% - {analytics['max_risk_used']:5.1f}%")
        
    else:
        print("No trades generated!")

if __name__ == '__main__':
    main()
