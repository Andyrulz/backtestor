import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from tqdm import tqdm

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

def get_dynamic_risk_percentage(consecutive_losses):
    """
    Calculate dynamic risk percentage based on consecutive losses
    
    Optimized Dynamic Risk Schedule:
    0-2 losses: 2.0% (Normal)
    3-4 losses: 1.6% (20% reduction)
    5-7 losses: 1.2% (40% reduction)
    8-11 losses: 0.8% (60% reduction)
    12-14 losses: 0.4% (80% reduction)
    15-17 losses: 0.2% (90% reduction)
    18+ losses: 0.1% (95% reduction - minimum floor)
    """
    if consecutive_losses >= 18:
        return 0.1  # Minimum risk floor
    elif consecutive_losses >= 15:
        return 0.2
    elif consecutive_losses >= 12:
        return 0.4
    elif consecutive_losses >= 8:
        return 0.8
    elif consecutive_losses >= 5:
        return 1.2
    elif consecutive_losses >= 3:
        return 1.6
    else:
        return 2.0  # Normal risk

def calculate_options_position_size(capital, consecutive_losses, sl_distance, entry_price):
    """
    Enhanced options position sizing with dynamic risk management
    
    Assumptions:
    - Option premium: ₹100 per contract (fixed)
    - Options leverage: 25x (for 1% futures move = 25% option move)
    - Dynamic position size based on consecutive losses
    - Base capital: ₹1,00,000
    """
    # Get dynamic risk percentage based on consecutive losses
    risk_percentage = get_dynamic_risk_percentage(consecutive_losses) / 100
    risk_amount = capital * risk_percentage
    
    option_premium = 100  # Fixed ₹100 per option contract
    options_leverage = 25  # 1% futures move = 25% option move
    
    # Risk per option if SL is hit
    # Simple calculation: sl_distance with leverage factor
    risk_per_option = sl_distance * (options_leverage / 100)  # Convert leverage to decimal
    
    if risk_per_option <= 0:
        return 1, risk_percentage * 100
        
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
    
    return max(1, position_size), risk_percentage * 100

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
    consecutive_losses = 0  # Track consecutive losses for dynamic sizing
    capital = 100000  # Starting capital ₹1,00,000
    
    # Setup logging for detailed validation
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.FileHandler(validation_file, 'w'),
            logging.StreamHandler()
        ]
    )
    
    # Sort pivots by datetime
    pivots = sorted(pivots, key=lambda x: x['datetime'])
    
    # Track for detailed logging
    detailed_logged = 0
    
    total_pivots = len(pivots)
    logging.info(f"Starting backtest with {total_pivots} pivots")
    logging.info(f"Dynamic Position Sizing: Active (Reset after 1 win)")
    logging.info(f"Base Capital: ₹{capital:,}")
    logging.info(f"Risk Schedule: 3,5,8,12,15,18+ losses → 1.6%,1.2%,0.8%,0.4%,0.2%,0.1%")
    logging.info("="*80)
    
    for idx, pivot in enumerate(tqdm(pivots, desc="Processing pivots")):
        current_time = pivot['datetime']
        
        # Find current index in dataframe
        current_idx = df[df['datetime'] <= current_time].index[-1]
        
        # Check for potential trade setups
        setup = find_trade_setup(df, current_idx, pivot)
        
        if setup['valid']:
            # Get dynamic position sizing based on consecutive losses
            position_size, current_risk_pct = calculate_options_position_size(
                capital, consecutive_losses, setup['sl_distance'], setup['entry_price']
            )
            
            # Create trade with dynamic sizing
            trade = {
                'entry_time': setup['entry_time'],
                'entry_price': setup['entry_price'],
                'direction': setup['direction'],
                'sl_price': setup['sl_price'],
                'tp_price': setup.get('tp_price'),
                'position_size': position_size,
                'consecutive_losses_at_entry': consecutive_losses,
                'risk_percentage': current_risk_pct,
                'marking_candle_time': setup['marking_candle_time'],
                'marking_candle_high': setup['marking_candle_high'],
                'marking_candle_low': setup['marking_candle_low'],
                'pivot_type': pivot['type'],
                'pivot_price': pivot['price'],
                'pivot_time': pivot['datetime'],
                'entry_idx': setup['entry_idx'],
                'status': 'open',
                'exit_reason': None,
                'exit_time': None,
                'exit_price': None,
                'pl_points': 0,
                'pl_rupees': 0
            }
            
            # Log detailed information for first few trades
            if detailed_logged < detailed_log_count:
                logging.info(f"\n--- TRADE {len(trades)+1} SETUP ---")
                logging.info(f"Pivot: {pivot['type']} at {pivot['price']} on {pivot['datetime']}")
                logging.info(f"Entry: {setup['direction']} at {setup['entry_price']} on {setup['entry_time']}")
                logging.info(f"SL: {setup['sl_price']}, TP: {setup.get('tp_price', 'Trailing')}")
                logging.info(f"Consecutive Losses: {consecutive_losses}")
                logging.info(f"Dynamic Risk: {current_risk_pct:.1f}%")
                logging.info(f"Position Size: {position_size} lots")
                logging.info(f"Risk Amount: ₹{capital * current_risk_pct / 100:.0f}")
                detailed_logged += 1
            
            open_trades.append(trade)
        
        # Process open trades for exits
        for trade in open_trades[:]:
            exit_result = check_trade_exit_pivot_trail(df, trade, current_idx)
            
            if exit_result['should_exit']:
                # Close the trade
                trade['exit_time'] = exit_result['exit_time']
                trade['exit_price'] = exit_result['exit_price']
                trade['exit_reason'] = exit_result['exit_reason']
                trade['status'] = 'closed'
                
                # Calculate P&L
                if trade['direction'] == 'long':
                    points_pl = trade['exit_price'] - trade['entry_price']
                else:
                    points_pl = trade['entry_price'] - trade['exit_price']
                
                trade['pl_points'] = points_pl
                trade['pl_rupees'] = points_pl * trade['position_size'] * 25  # 25x leverage
                
                # Update consecutive losses counter
                if points_pl > 0:
                    consecutive_losses = 0  # Reset after any win
                else:
                    consecutive_losses += 1  # Increment after loss
                
                # Update capital (for position sizing calculation)
                capital += trade['pl_rupees']
                
                # Log trade completion
                if len(trades) < detailed_log_count:
                    logging.info(f"Trade closed: {exit_result['exit_reason']}")
                    logging.info(f"P&L: {points_pl:.1f} points, ₹{trade['pl_rupees']:.0f}")
                    logging.info(f"New consecutive losses: {consecutive_losses}")
                    logging.info(f"Updated capital: ₹{capital:.0f}")
                
                trades.append(trade)
                open_trades.remove(trade)
        
        # Close all open trades at end of day (3:30 PM)
        if current_time.time() >= pd.to_datetime('15:25').time():
            for trade in open_trades[:]:
                current_price = df.iloc[current_idx]['close']
                
                trade['exit_time'] = current_time
                trade['exit_price'] = current_price
                trade['exit_reason'] = 'EOD_CLOSE'
                trade['status'] = 'closed'
                
                # Calculate P&L
                if trade['direction'] == 'long':
                    points_pl = trade['exit_price'] - trade['entry_price']
                else:
                    points_pl = trade['entry_price'] - trade['exit_price']
                
                trade['pl_points'] = points_pl
                trade['pl_rupees'] = points_pl * trade['position_size'] * 25
                
                # Update consecutive losses
                if points_pl > 0:
                    consecutive_losses = 0
                else:
                    consecutive_losses += 1
                
                capital += trade['pl_rupees']
                
                trades.append(trade)
                open_trades.remove(trade)
    
    logging.info(f"\nBacktest completed. Total trades: {len(trades)}")
    logging.info(f"Final consecutive losses: {consecutive_losses}")
    logging.info(f"Final capital: ₹{capital:.0f}")
    
    return trades

def find_trade_setup(df, current_idx, pivot):
    """Enhanced trade setup finder with dynamic risk management"""
    setup = {'valid': False}
    
    if current_idx >= len(df) - 1:
        return setup
    
    current_time = df.iloc[current_idx]['datetime']
    current_price = df.iloc[current_idx]['close']
    
    # Look for breakout pattern
    if pivot['type'] == 'high':
        # Long breakout setup
        if (df.iloc[current_idx]['high'] > pivot['price'] and 
            df.iloc[current_idx]['close'] > df.iloc[current_idx]['open']):
            
            # Look for marking candle in next 5 bars
            for i in range(1, 6):
                if current_idx + i >= len(df):
                    break
                    
                next_bar = df.iloc[current_idx + i]
                if (next_bar['close'] < next_bar['open'] and  # Red candle
                    df.iloc[current_idx]['low'] <= next_bar['close'] <= df.iloc[current_idx]['high']):
                    
                    entry_price = next_bar['high'] + 0.1
                    sl_price = next_bar['low']
                    sl_distance = abs(entry_price - sl_price)
                    
                    # Check 0.1% SL distance limit
                    if sl_distance <= entry_price * 0.001:
                        setup = {
                            'valid': True,
                            'direction': 'long',
                            'entry_price': entry_price,
                            'sl_price': sl_price,
                            'sl_distance': sl_distance,
                            'entry_time': next_bar['datetime'],
                            'entry_idx': current_idx + i,
                            'marking_candle_time': next_bar['datetime'],
                            'marking_candle_high': next_bar['high'],
                            'marking_candle_low': next_bar['low']
                        }
                        break
                        
    elif pivot['type'] == 'low':
        # Short breakout setup
        if (df.iloc[current_idx]['low'] < pivot['price'] and 
            df.iloc[current_idx]['close'] < df.iloc[current_idx]['open']):
            
            # Look for marking candle in next 5 bars
            for i in range(1, 6):
                if current_idx + i >= len(df):
                    break
                    
                next_bar = df.iloc[current_idx + i]
                if (next_bar['close'] > next_bar['open'] and  # Green candle
                    df.iloc[current_idx]['low'] <= next_bar['close'] <= df.iloc[current_idx]['high']):
                    
                    entry_price = next_bar['low'] - 0.1
                    sl_price = next_bar['high']
                    sl_distance = abs(sl_price - entry_price)
                    
                    # Check 0.1% SL distance limit
                    if sl_distance <= entry_price * 0.001:
                        setup = {
                            'valid': True,
                            'direction': 'short',
                            'entry_price': entry_price,
                            'sl_price': sl_price,
                            'sl_distance': sl_distance,
                            'entry_time': next_bar['datetime'],
                            'entry_idx': current_idx + i,
                            'marking_candle_time': next_bar['datetime'],
                            'marking_candle_high': next_bar['high'],
                            'marking_candle_low': next_bar['low']
                        }
                        break
    
    return setup

def check_trade_exit_pivot_trail(df, trade, current_idx):
    """Enhanced exit checker with dynamic position sizing tracking"""
    result = {'should_exit': False, 'exit_reason': None, 'exit_time': None, 'exit_price': None}
    
    if current_idx >= len(df):
        return result
    
    current_bar = df.iloc[current_idx]
    direction = trade['direction']
    sl_price = trade['sl_price']
    entry_price = trade['entry_price']
    current_price = current_bar['close']
    
    # Get current 1-minute pivot level for trailing
    trailing_level = get_trailing_pivot_level(df, current_idx, direction, current_price, trade['entry_idx'])
    
    if direction == 'long':
        # Check original SL first
        if current_bar['low'] <= sl_price:
            result = {
                'should_exit': True,
                'exit_reason': 'SL',
                'exit_time': current_bar['datetime'],
                'exit_price': sl_price
            }
        # Check pivot trailing stop
        elif trailing_level is not None:
            if trailing_level > sl_price:  # Only use if higher than original SL
                if current_bar['low'] <= trailing_level:
                    result = {
                        'should_exit': True,
                        'exit_reason': 'PIVOT_TRAIL',
                        'exit_time': current_bar['datetime'],
                        'exit_price': trailing_level
                    }
                    
    else:  # short
        # Check original SL first
        if current_bar['high'] >= sl_price:
            result = {
                'should_exit': True,
                'exit_reason': 'SL',
                'exit_time': current_bar['datetime'],
                'exit_price': sl_price
            }
        # Check pivot trailing stop
        elif trailing_level is not None:
            if trailing_level < sl_price:  # Only use if lower than original SL
                if current_bar['high'] >= trailing_level:
                    result = {
                        'should_exit': True,
                        'exit_reason': 'PIVOT_TRAIL',
                        'exit_time': current_bar['datetime'],
                        'exit_price': trailing_level
                    }
    
    return result

def calculate_analytics(trades):
    """Calculate comprehensive analytics for dynamic sizing results"""
    if not trades:
        return {"message": "No trades to analyze"}
    
    # Basic statistics
    total_trades = len(trades)
    wins = sum(1 for t in trades if t['pl_points'] > 0)
    losses = total_trades - wins
    win_rate = wins / total_trades * 100
    
    # P&L statistics
    total_pl_points = sum(t['pl_points'] for t in trades)
    total_pl_rupees = sum(t['pl_rupees'] for t in trades)
    
    winning_trades = [t for t in trades if t['pl_points'] > 0]
    losing_trades = [t for t in trades if t['pl_points'] <= 0]
    
    avg_win = np.mean([t['pl_points'] for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t['pl_points'] for t in losing_trades]) if losing_trades else 0
    
    # Risk management statistics
    avg_risk = np.mean([t['risk_percentage'] for t in trades])
    avg_position_size = np.mean([t['position_size'] for t in trades])
    
    # Consecutive losses analysis
    max_consecutive_losses = 0
    current_consecutive = 0
    for trade in trades:
        if trade['pl_points'] <= 0:
            current_consecutive += 1
            max_consecutive_losses = max(max_consecutive_losses, current_consecutive)
        else:
            current_consecutive = 0
    
    # Capital efficiency
    initial_capital = 100000
    final_capital = initial_capital + total_pl_rupees
    
    # CAGR calculation
    first_trade_date = pd.to_datetime(trades[0]['entry_time'])
    last_trade_date = pd.to_datetime(trades[-1]['exit_time'])
    total_days = (last_trade_date - first_trade_date).days
    
    if total_days > 0 and final_capital > 0:
        cagr = ((final_capital / initial_capital) ** (365.25 / total_days) - 1) * 100
    else:
        cagr = 0
    
    # Drawdown calculation
    cumulative_pl = np.cumsum([t['pl_rupees'] for t in trades])
    peak = np.maximum.accumulate(cumulative_pl)
    drawdown = peak - cumulative_pl
    max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
    
    return {
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'win_rate': round(win_rate, 2),
        'total_pl_points': round(total_pl_points, 1),
        'total_pl_rupees': round(total_pl_rupees, 0),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'avg_risk_percentage': round(avg_risk, 2),
        'avg_position_size': round(avg_position_size, 1),
        'max_consecutive_losses': max_consecutive_losses,
        'initial_capital': initial_capital,
        'final_capital': round(final_capital, 0),
        'total_return': round((final_capital - initial_capital) / initial_capital * 100, 2),
        'cagr': round(cagr, 2),
        'max_drawdown': round(max_drawdown, 0),
        'total_days': total_days
    }

if __name__ == "__main__":
    print("=" * 80)
    print("5-MINUTE PIVOT BREAKOUT STRATEGY - DYNAMIC POSITION SIZING")
    print("=" * 80)
    print("Loading data...")
    
    # Load 1-minute NIFTY data
    df = load_data('NIFTY 50_minute_data.csv')
    print(f"Loaded {len(df)} 1-minute bars")
    
    # Calculate 5-minute pivots
    print("Calculating 5-minute pivots...")
    pivots = calculate_pivots(df)
    print(f"Found {len(pivots)} 5-minute pivots")
    
    # Run backtest with dynamic position sizing
    print("Running backtest with dynamic position sizing...")
    trades = backtest_strategy(df, pivots)
    
    # Save results
    df_trades = pd.DataFrame(trades)
    df_trades.to_csv('backtest_results_dynamic_sizing.csv', index=False)
    
    # Calculate and display results
    if len(trades) > 0:
        total_pl_points = df_trades['pl_points'].sum()
        total_pl_rupees = df_trades['pl_rupees'].sum()
        winning_trades = len(df_trades[df_trades['pl_points'] > 0])
        losing_trades = len(df_trades[df_trades['pl_points'] <= 0])
        win_rate = (winning_trades / len(trades)) * 100
        
        avg_risk = df_trades['risk_percentage'].mean()
        
        print("\n" + "=" * 80)
        print("DYNAMIC POSITION SIZING BACKTEST RESULTS")
        print("=" * 80)
        print(f"Total Trades: {len(trades)}")
        print(f"Winning Trades: {winning_trades}")
        print(f"Losing Trades: {losing_trades}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Total P&L (Points): {total_pl_points:.1f}")
        print(f"Total P&L (Rupees): ₹{total_pl_rupees:,.0f}")
        print(f"Average Risk Per Trade: {avg_risk:.2f}%")
        print(f"Risk Reduction: {((avg_risk/2.0)-1)*100:+.1f}%")
        
        # Risk distribution
        risk_dist = df_trades['risk_percentage'].value_counts().sort_index()
        print(f"\nRisk Distribution:")
        for risk, count in risk_dist.items():
            percentage = (count / len(trades)) * 100
            print(f"  {risk:4.1f}% risk: {count:4d} trades ({percentage:5.1f}%)")
        
        print(f"\nResults saved to: backtest_results_dynamic_sizing.csv")
    else:
        print("No trades generated!")
