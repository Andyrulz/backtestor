import pandas as pd
import numpy as np
from datetime import datetime
import csv

def get_smart_risk_percentage(sl_distance, entry_hour, direction, consecutive_losses_at_entry):
    """
    Calculate smart risk percentage based on setup quality indicators.
    
    Args:
        sl_distance: Stop loss distance in points
        entry_hour: Hour of trade entry (0-23)
        direction: 'long' or 'short'
        consecutive_losses_at_entry: Number of consecutive losses at trade entry
    
    Returns:
        risk_percentage: Smart risk percentage (0.005 to 0.04 = 0.5% to 4.0%)
    """
    base_risk = 0.02  # 2% base risk
    
    # 1. SETUP QUALITY MULTIPLIER (based on SL distance - primary factor)
    if sl_distance <= 7:
        setup_quality_multiplier = 1.5  # High quality tight setups
    elif sl_distance <= 10:
        setup_quality_multiplier = 1.25  # Good quality setups
    elif sl_distance > 15:
        setup_quality_multiplier = 0.75  # Poor quality wide setups
    else:
        setup_quality_multiplier = 1.0   # Average setups
    
    # 2. TIMING MULTIPLIER (based on optimal entry hours)
    optimal_hours = [11, 12, 14]  # Best performing hours from analysis
    poor_hours = [10, 15]         # Worst performing hours
    
    if entry_hour in optimal_hours:
        timing_multiplier = 1.2  # 20% bonus for optimal timing
    elif entry_hour in poor_hours:
        timing_multiplier = 0.8  # 20% reduction for poor timing
    else:
        timing_multiplier = 1.0  # Neutral timing
    
    # 3. DIRECTION BIAS MULTIPLIER (longs perform better)
    if direction == 'long':
        direction_multiplier = 1.1  # 10% bonus for long trades
    else:
        direction_multiplier = 0.95  # 5% reduction for short trades
    
    # 4. CONSECUTIVE LOSS PROTECTION (overlay from previous system)
    # Reduce risk based on consecutive losses (same logic as before)
    if consecutive_losses_at_entry >= 18:
        loss_protection_multiplier = 0.05  # 0.1% minimum risk
    elif consecutive_losses_at_entry >= 15:
        loss_protection_multiplier = 0.1   # 0.2% risk
    elif consecutive_losses_at_entry >= 12:
        loss_protection_multiplier = 0.2   # 0.4% risk
    elif consecutive_losses_at_entry >= 8:
        loss_protection_multiplier = 0.4   # 0.8% risk
    elif consecutive_losses_at_entry >= 5:
        loss_protection_multiplier = 0.6   # 1.2% risk
    elif consecutive_losses_at_entry >= 3:
        loss_protection_multiplier = 0.8   # 1.6% risk
    else:
        loss_protection_multiplier = 1.0   # No reduction
    
    # Calculate final risk percentage
    smart_risk = base_risk * setup_quality_multiplier * timing_multiplier * direction_multiplier
    
    # Apply consecutive loss protection as minimum of smart risk or protection limit
    if loss_protection_multiplier < 1.0:
        protection_risk = base_risk * loss_protection_multiplier
        smart_risk = min(smart_risk, protection_risk)
    
    # Cap the risk between 0.5% and 4.0%
    smart_risk = max(0.005, min(0.04, smart_risk))
    
    return smart_risk

def run_smart_position_sizing_backtest():
    """Run backtest with smart position sizing system"""
    
    print("="*80)
    print("RUNNING SMART POSITION SIZING BACKTEST")
    print("="*80)
    
    # Load original trades to get all the trade setups
    trades_df = pd.read_csv('backtest_results_pivot_trail.csv')
    
    print(f"Loaded {len(trades_df)} trades for smart sizing backtest")
    
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
        
        # Calculate smart risk percentage
        smart_risk_pct = get_smart_risk_percentage(
            sl_distance, entry_hour, direction, consecutive_losses
        )
        
        # Calculate position size based on smart risk
        risk_amount = current_capital * smart_risk_pct
        
        # Position sizing: risk_amount / sl_distance (same formula, but dynamic risk%)
        if sl_distance > 0:
            position_size = risk_amount / sl_distance
        else:
            position_size = 0
        
        # Calculate actual P&L in rupees
        actual_pl = pl_points * position_size
        
        # Update capital
        new_capital = current_capital + actual_pl
        
        # Track consecutive losses
        if pl_points > 0:
            consecutive_losses = 0  # Reset on win
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
            'smart_risk_percentage': smart_risk_pct,
            'consecutive_losses_at_entry': consecutive_losses,
            'position_size': position_size,
            'entry_hour': entry_hour
        }
        
        results.append(result)
        current_capital = new_capital
        
        # Progress update
        if (idx + 1) % 500 == 0:
            print(f"Processed {idx + 1} trades, Capital: ₹{current_capital:,.0f}")
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Save results
    output_file = 'backtest_results_smart_sizing.csv'
    results_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Backtest completed!")
    print(f"📁 Results saved to: {output_file}")
    print(f"💰 Final Capital: ₹{current_capital:,.0f}")
    print(f"📈 Total Return: {((current_capital - initial_capital) / initial_capital) * 100:.1f}%")
    
    return results_df

def analyze_smart_sizing_results():
    """Analyze and compare smart sizing results with previous strategies"""
    
    print("\n" + "="*80)
    print("SMART POSITION SIZING ANALYSIS & COMPARISON")
    print("="*80)
    
    # Load all strategy results
    original_df = pd.read_csv('backtest_results_pivot_trail.csv')
    dynamic_df = pd.read_csv('backtest_results_pivot_trail_dynamic.csv')
    smart_df = pd.read_csv('backtest_results_smart_sizing.csv')
    
    strategies = {
        'Original (Fixed 2%)': original_df,
        'Dynamic (Loss-based)': dynamic_df,
        'Smart (Setup Quality)': smart_df
    }
    
    print(f"\n{'📊 COMPREHENSIVE STRATEGY COMPARISON':<60}")
    print("=" * 80)
    
    comparison_results = {}
    
    for name, df in strategies.items():
        # Basic metrics
        total_trades = len(df)
        wins = len(df[df['pl_points'] > 0])
        losses = len(df[df['pl_points'] <= 0])
        win_rate = (wins / total_trades) * 100
        
        # P&L metrics
        total_pl_points = df['pl_points'].sum()
        final_capital = df['exit_capital'].iloc[-1]
        total_return = ((final_capital - 100000) / 100000) * 100
        
        # Calculate CAGR
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
        
        # Drawdown calculation
        running_pl = df['pl_points'].cumsum()
        peak = running_pl.cummax()
        drawdown = peak - running_pl
        max_drawdown_points = drawdown.max()
        
        # Capital drawdown
        capital_curve = df['exit_capital'].values
        capital_peak = np.maximum.accumulate(capital_curve)
        capital_drawdown = (capital_peak - capital_curve) / capital_peak * 100
        max_capital_drawdown = capital_drawdown.max()
        
        # Store results
        comparison_results[name] = {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pl_points': total_pl_points,
            'final_capital': final_capital,
            'total_return': total_return,
            'cagr': cagr,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown_points': max_drawdown_points,
            'max_capital_drawdown': max_capital_drawdown
        }
    
    # Display comparison table
    print(f"\n{'Strategy Performance Comparison:':<40}")
    print("-" * 120)
    print(f"{'Metric':<25} {'Original':<20} {'Dynamic':<20} {'Smart':<20} {'Best':<15}")
    print("-" * 120)
    
    metrics_to_compare = [
        ('Total Trades', 'total_trades', '{:.0f}', 'higher'),
        ('Win Rate (%)', 'win_rate', '{:.2f}', 'higher'),
        ('Total P&L (pts)', 'total_pl_points', '{:.1f}', 'higher'),
        ('Final Capital (₹)', 'final_capital', '{:,.0f}', 'higher'),
        ('Total Return (%)', 'total_return', '{:.1f}', 'higher'),
        ('CAGR (%)', 'cagr', '{:.1f}', 'higher'),
        ('Avg Win (pts)', 'avg_win', '{:.1f}', 'higher'),
        ('Avg Loss (pts)', 'avg_loss', '{:.1f}', 'higher'),
        ('Profit Factor', 'profit_factor', '{:.2f}', 'higher'),
        ('Max DD (pts)', 'max_drawdown_points', '{:.1f}', 'lower'),
        ('Max Cap DD (%)', 'max_capital_drawdown', '{:.2f}', 'lower')
    ]
    
    strategy_names = ['Original (Fixed 2%)', 'Dynamic (Loss-based)', 'Smart (Setup Quality)']
    
    for metric_name, metric_key, format_str, direction in metrics_to_compare:
        values = [comparison_results[name][metric_key] for name in strategy_names]
        formatted_values = [format_str.format(v) for v in values]
        
        # Find best performer
        if direction == 'higher':
            best_idx = np.argmax(values)
        else:
            best_idx = np.argmin(values)
        
        best_strategy = strategy_names[best_idx].split(' ')[0]
        
        print(f"{metric_name:<25} {formatted_values[0]:<20} {formatted_values[1]:<20} {formatted_values[2]:<20} {best_strategy:<15}")
    
    # Risk distribution analysis for smart sizing
    if 'smart_risk_percentage' in smart_df.columns:
        print(f"\n{'🎯 SMART SIZING RISK DISTRIBUTION':<60}")
        print("-" * 70)
        
        risk_distribution = smart_df['smart_risk_percentage'].value_counts().sort_index()
        print("Risk percentage distribution in Smart Strategy:")
        
        for risk_pct in sorted(risk_distribution.index):
            count = risk_distribution[risk_pct]
            percentage = (count / len(smart_df)) * 100
            print(f"  {risk_pct*100:>5.1f}% risk: {count:>4d} trades ({percentage:>5.1f}%)")
        
        avg_risk = smart_df['smart_risk_percentage'].mean() * 100
        print(f"\nAverage risk used: {avg_risk:.2f}%")
        
        # Compare with baseline 2%
        risk_efficiency = avg_risk / 2.0
        print(f"Risk efficiency vs baseline: {risk_efficiency:.2f}x")
    
    # Performance improvement analysis
    print(f"\n{'📈 IMPROVEMENT ANALYSIS':<60}")
    print("-" * 70)
    
    original_final = comparison_results['Original (Fixed 2%)']['final_capital']
    dynamic_final = comparison_results['Dynamic (Loss-based)']['final_capital']
    smart_final = comparison_results['Smart (Setup Quality)']['final_capital']
    
    dynamic_improvement = ((dynamic_final - original_final) / original_final) * 100
    smart_improvement = ((smart_final - original_final) / original_final) * 100
    smart_vs_dynamic = ((smart_final - dynamic_final) / dynamic_final) * 100
    
    print(f"Performance improvements over Original strategy:")
    print(f"  Dynamic sizing: {dynamic_improvement:+.2f}%")
    print(f"  Smart sizing:   {smart_improvement:+.2f}%")
    print(f"  Smart vs Dynamic: {smart_vs_dynamic:+.2f}%")
    
    print(f"\nAbsolute capital differences:")
    print(f"  Smart vs Original: ₹{smart_final - original_final:+,.0f}")
    print(f"  Smart vs Dynamic:  ₹{smart_final - dynamic_final:+,.0f}")
    
    # Best strategy summary
    best_capital = max(original_final, dynamic_final, smart_final)
    if best_capital == smart_final:
        best_strategy = "Smart (Setup Quality)"
    elif best_capital == dynamic_final:
        best_strategy = "Dynamic (Loss-based)"
    else:
        best_strategy = "Original (Fixed 2%)"
    
    print(f"\n{'🏆 FINAL VERDICT':<60}")
    print("=" * 70)
    print(f"WINNER: {best_strategy}")
    print(f"Final Capital: ₹{best_capital:,.0f}")
    
    best_cagr = comparison_results[best_strategy]['cagr']
    print(f"CAGR: {best_cagr:.1f}%")
    
    return comparison_results

if __name__ == "__main__":
    # Run smart position sizing backtest
    smart_results = run_smart_position_sizing_backtest()
    
    # Analyze and compare results
    comparison = analyze_smart_sizing_results()
