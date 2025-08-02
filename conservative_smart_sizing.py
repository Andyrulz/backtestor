import pandas as pd
import numpy as np

def create_conservative_smart_sizing():
    """Create a more conservative version of smart sizing with caps"""
    
    print("="*80)
    print("CREATING CONSERVATIVE SMART POSITION SIZING")
    print("="*80)
    
    # Load original trades
    trades_df = pd.read_csv('backtest_results_pivot_trail.csv')
    
    # Initialize capital and tracking
    initial_capital = 100000
    current_capital = initial_capital
    consecutive_losses = 0
    
    results = []
    
    for idx, trade in trades_df.iterrows():
        # Extract trade details
        sl_distance = trade['sl_distance']
        pl_points = trade['pl_points']
        entry_time = pd.to_datetime(trade['entry_time'])
        entry_hour = entry_time.hour
        direction = trade['direction']
        
        # CONSERVATIVE SMART RISK CALCULATION
        base_risk = 0.02  # 2% base risk
        
        # 1. Setup quality (more conservative multipliers)
        if sl_distance <= 7:
            setup_multiplier = 1.25  # 25% increase instead of 50%
        elif sl_distance <= 10:
            setup_multiplier = 1.1   # 10% increase
        elif sl_distance > 15:
            setup_multiplier = 0.8   # 20% reduction
        else:
            setup_multiplier = 1.0
        
        # 2. Timing (smaller adjustments)
        optimal_hours = [11, 12, 14]
        poor_hours = [10, 15]
        
        if entry_hour in optimal_hours:
            timing_multiplier = 1.1  # 10% bonus
        elif entry_hour in poor_hours:
            timing_multiplier = 0.9  # 10% reduction
        else:
            timing_multiplier = 1.0
        
        # 3. Direction bias (minimal)
        if direction == 'long':
            direction_multiplier = 1.05  # 5% bonus
        else:
            direction_multiplier = 0.98  # 2% reduction
        
        # 4. Consecutive loss protection
        if consecutive_losses >= 18:
            loss_protection = 0.1
        elif consecutive_losses >= 15:
            loss_protection = 0.2
        elif consecutive_losses >= 12:
            loss_protection = 0.4
        elif consecutive_losses >= 8:
            loss_protection = 0.6
        elif consecutive_losses >= 5:
            loss_protection = 0.8
        elif consecutive_losses >= 3:
            loss_protection = 0.9
        else:
            loss_protection = 1.0
        
        # Calculate smart risk
        smart_risk = base_risk * setup_multiplier * timing_multiplier * direction_multiplier
        
        # Apply loss protection
        if loss_protection < 1.0:
            protection_risk = base_risk * loss_protection
            smart_risk = min(smart_risk, protection_risk)
        
        # CONSERVATIVE CAPS: 0.5% to 2.5% (instead of 0.5% to 4.0%)
        smart_risk = max(0.005, min(0.025, smart_risk))
        
        # Calculate position size
        risk_amount = current_capital * smart_risk
        
        if sl_distance > 0:
            position_size = risk_amount / sl_distance
        else:
            position_size = 0
        
        # Calculate P&L
        actual_pl = pl_points * position_size
        new_capital = current_capital + actual_pl
        
        # Update consecutive losses
        if pl_points > 0:
            consecutive_losses = 0
        else:
            consecutive_losses += 1
        
        # Store results
        result = {
            'trade_num': trade['trade_num'],
            'breakout_time': trade['breakout_time'],
            'entry_time': trade['entry_time'],
            'exit_time': trade['exit_time'],
            'direction': direction,
            'pivot_level': trade['pivot_level'],
            'entry_price': trade['entry_price'],
            'sl_price': trade['sl_price'],
            'tp_price': trade['tp_price'],
            'exit_price': trade['exit_price'],
            'result': trade['result'],
            'pl_points': pl_points,
            'sl_distance': sl_distance,
            'rr_achieved': trade['rr_achieved'],
            'max_favorable': trade['max_favorable'],
            'max_adverse': trade['max_adverse'],
            'max_rr_potential': trade['max_rr_potential'],
            'time_in_trade_minutes': trade['time_in_trade_minutes'],
            'marking_updates': trade['marking_updates'],
            'exit_size': trade['exit_size'],
            'rr_target_achieved': trade['rr_target_achieved'],
            'actual_pl': actual_pl,
            'entry_capital': current_capital,
            'exit_capital': new_capital,
            'conservative_risk_percentage': smart_risk,
            'consecutive_losses_at_entry': consecutive_losses,
            'position_size': position_size,
            'entry_hour': entry_hour
        }
        
        results.append(result)
        current_capital = new_capital
        
        if (idx + 1) % 500 == 0:
            print(f"Processed {idx + 1} trades, Capital: ₹{current_capital:,.0f}")
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv('backtest_results_conservative_smart.csv', index=False)
    
    print(f"\n✅ Conservative Smart Sizing completed!")
    print(f"💰 Final Capital: ₹{current_capital:,.0f}")
    print(f"📈 Total Return: {((current_capital - initial_capital) / initial_capital) * 100:.1f}%")
    
    return results_df

def comprehensive_strategy_comparison():
    """Compare all four strategies comprehensively"""
    
    print("\n" + "="*80)
    print("COMPREHENSIVE 4-STRATEGY COMPARISON")
    print("="*80)
    
    # Load all strategy results
    strategies = {
        'Original (Fixed 2%)': pd.read_csv('backtest_results_pivot_trail.csv'),
        'Dynamic (Loss Protection)': pd.read_csv('backtest_results_pivot_trail_dynamic.csv'),
        'Smart (Aggressive)': pd.read_csv('backtest_results_smart_sizing.csv'),
        'Smart (Conservative)': pd.read_csv('backtest_results_conservative_smart.csv')
    }
    
    print(f"\n{'PERFORMANCE COMPARISON TABLE':<80}")
    print("=" * 120)
    
    # Calculate metrics for each strategy
    results_table = []
    
    for name, df in strategies.items():
        # Basic metrics
        total_trades = len(df)
        wins = len(df[df['pl_points'] > 0])
        win_rate = (wins / total_trades) * 100
        
        # P&L metrics
        total_pl_points = df['pl_points'].sum()
        final_capital = df['exit_capital'].iloc[-1]
        total_return = ((final_capital - 100000) / 100000) * 100
        
        # CAGR calculation
        start_date = pd.to_datetime(df['entry_time'].iloc[0])
        end_date = pd.to_datetime(df['exit_time'].iloc[-1])
        years = (end_date - start_date).days / 365.25
        cagr = ((final_capital / 100000) ** (1/years) - 1) * 100
        
        # Risk metrics
        winning_trades = df[df['pl_points'] > 0]
        losing_trades = df[df['pl_points'] <= 0]
        
        avg_win = winning_trades['pl_points'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['pl_points'].mean() if len(losing_trades) > 0 else 0
        
        win_pl = winning_trades['pl_points'].sum()
        loss_pl = abs(losing_trades['pl_points'].sum())
        profit_factor = win_pl / loss_pl if loss_pl > 0 else float('inf')
        
        # Drawdown
        running_pl = df['pl_points'].cumsum()
        peak = running_pl.cummax()
        drawdown = peak - running_pl
        max_drawdown_points = drawdown.max()
        
        # Capital drawdown
        capital_curve = df['exit_capital'].values
        capital_peak = np.maximum.accumulate(capital_curve)
        capital_drawdown = (capital_peak - capital_curve) / capital_peak * 100
        max_capital_drawdown = capital_drawdown.max()
        
        # Average risk used (if available)
        if 'smart_risk_percentage' in df.columns:
            avg_risk = df['smart_risk_percentage'].mean() * 100
        elif 'conservative_risk_percentage' in df.columns:
            avg_risk = df['conservative_risk_percentage'].mean() * 100
        elif 'risk_percentage' in df.columns:
            avg_risk = df['risk_percentage'].mean() * 100
        else:
            avg_risk = 2.0  # Fixed 2%
        
        results_table.append({
            'Strategy': name,
            'Trades': total_trades,
            'Win Rate (%)': win_rate,
            'Total P&L (pts)': total_pl_points,
            'Final Capital (₹)': final_capital,
            'Total Return (%)': total_return,
            'CAGR (%)': cagr,
            'Avg Risk (%)': avg_risk,
            'Profit Factor': profit_factor,
            'Max DD (pts)': max_drawdown_points,
            'Max Cap DD (%)': max_capital_drawdown
        })
    
    # Create comparison DataFrame
    comparison_df = pd.DataFrame(results_table)
    
    # Display formatted table
    print(f"{'Strategy':<25} {'Final Capital (₹)':<18} {'CAGR (%)':<10} {'Max DD (%)':<12} {'Avg Risk (%)':<12}")
    print("-" * 80)
    
    for _, row in comparison_df.iterrows():
        print(f"{row['Strategy']:<25} {row['Final Capital (₹)']:>15,.0f} {row['CAGR (%)']:>8.1f} {row['Max Cap DD (%)']:>10.1f} {row['Avg Risk (%)']:>10.1f}")
    
    # Detailed metrics table
    print(f"\n{'DETAILED METRICS COMPARISON':<80}")
    print("=" * 140)
    
    metrics_order = ['Trades', 'Win Rate (%)', 'Total P&L (pts)', 'Final Capital (₹)', 
                    'Total Return (%)', 'CAGR (%)', 'Profit Factor', 'Max DD (pts)', 'Max Cap DD (%)']
    
    for metric in metrics_order:
        print(f"{metric:<20}", end="")
        for _, row in comparison_df.iterrows():
            if 'Capital' in metric or 'Return' in metric:
                print(f"{row[metric]:>20,.0f}", end="")
            elif '(%)' in metric or 'Factor' in metric:
                print(f"{row[metric]:>20.2f}", end="")
            else:
                print(f"{row[metric]:>20.0f}", end="")
        print()
    
    # Find the best strategy by different criteria
    print(f"\n{'BEST STRATEGY BY CRITERIA':<60}")
    print("-" * 60)
    
    best_capital_idx = comparison_df['Final Capital (₹)'].idxmax()
    best_cagr_idx = comparison_df['CAGR (%)'].idxmax()
    best_drawdown_idx = comparison_df['Max Cap DD (%)'].idxmin()
    best_risk_adj_idx = (comparison_df['CAGR (%)'] / comparison_df['Max Cap DD (%)']).idxmax()
    
    print(f"Best Final Capital: {comparison_df.loc[best_capital_idx, 'Strategy']}")
    print(f"Best CAGR: {comparison_df.loc[best_cagr_idx, 'Strategy']}")
    print(f"Best Drawdown: {comparison_df.loc[best_drawdown_idx, 'Strategy']}")
    print(f"Best Risk-Adjusted: {comparison_df.loc[best_risk_adj_idx, 'Strategy']}")
    
    # Save comparison to CSV
    comparison_df.to_csv('strategy_comparison_summary.csv', index=False)
    print(f"\n📁 Detailed comparison saved to: strategy_comparison_summary.csv")
    
    return comparison_df

if __name__ == "__main__":
    # Create conservative smart sizing
    conservative_results = create_conservative_smart_sizing()
    
    # Run comprehensive comparison
    comparison = comprehensive_strategy_comparison()
