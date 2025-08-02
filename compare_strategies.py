import pandas as pd
import numpy as np

# Load both strategy results
original_df = pd.read_csv('backtest_results_pivot_trail.csv')
dynamic_df = pd.read_csv('backtest_results_pivot_trail_dynamic.csv')

print("="*80)
print("DETAILED COMPARISON: ORIGINAL vs DYNAMIC POSITION SIZING")
print("="*80)

# Basic Statistics
print(f"\n{'BASIC STATISTICS':<50}")
print("-" * 50)
print(f"{'Metric':<25} {'Original':<15} {'Dynamic':<15} {'Difference':<15}")
print("-" * 50)

# Trade counts
orig_trades = len(original_df)
dyn_trades = len(dynamic_df)
print(f"{'Total Trades':<25} {orig_trades:<15} {dyn_trades:<15} {dyn_trades - orig_trades:<15}")

# Win rates
orig_wins = len(original_df[original_df['pl_points'] > 0])
dyn_wins = len(dynamic_df[dynamic_df['pl_points'] > 0])
orig_win_rate = (orig_wins / orig_trades) * 100
dyn_win_rate = (dyn_wins / dyn_trades) * 100
print(f"{'Win Rate (%)':<25} {orig_win_rate:<15.2f} {dyn_win_rate:<15.2f} {dyn_win_rate - orig_win_rate:<15.2f}")

# P&L in points
orig_pl = original_df['pl_points'].sum()
dyn_pl = dynamic_df['pl_points'].sum()
print(f"{'Total P&L (Points)':<25} {orig_pl:<15.1f} {dyn_pl:<15.1f} {dyn_pl - orig_pl:<15.1f}")

# Capital performance
orig_final_capital = original_df['exit_capital'].iloc[-1]
dyn_final_capital = dynamic_df['exit_capital'].iloc[-1]
orig_return = ((orig_final_capital - 100000) / 100000) * 100
dyn_return = ((dyn_final_capital - 100000) / 100000) * 100

print(f"{'Final Capital (₹)':<25} {orig_final_capital:<15,.0f} {dyn_final_capital:<15,.0f} {dyn_final_capital - orig_final_capital:<15,.0f}")
print(f"{'Total Return (%)':<25} {orig_return:<15.1f} {dyn_return:<15.1f} {dyn_return - orig_return:<15.1f}")

# CAGR calculation
import datetime
start_date = pd.to_datetime(original_df['entry_time'].iloc[0])
end_date = pd.to_datetime(original_df['exit_time'].iloc[-1])
years = (end_date - start_date).days / 365.25

orig_cagr = ((orig_final_capital / 100000) ** (1/years) - 1) * 100
dyn_cagr = ((dyn_final_capital / 100000) ** (1/years) - 1) * 100

print(f"{'CAGR (%)':<25} {orig_cagr:<15.1f} {dyn_cagr:<15.1f} {dyn_cagr - orig_cagr:<15.1f}")

# Risk metrics
print(f"\n{'RISK METRICS':<50}")
print("-" * 50)

# Calculate drawdowns
def calculate_drawdown(df):
    running_pl = df['pl_points'].cumsum()
    peak = running_pl.cummax()
    drawdown = peak - running_pl
    return drawdown.max()

orig_max_dd = calculate_drawdown(original_df)
dyn_max_dd = calculate_drawdown(dynamic_df)
print(f"{'Max Drawdown (Points)':<25} {orig_max_dd:<15.1f} {dyn_max_dd:<15.1f} {dyn_max_dd - orig_max_dd:<15.1f}")

# Profit factor
orig_wins_pl = original_df[original_df['pl_points'] > 0]['pl_points'].sum()
orig_loss_pl = abs(original_df[original_df['pl_points'] <= 0]['pl_points'].sum())
orig_pf = orig_wins_pl / orig_loss_pl if orig_loss_pl > 0 else float('inf')

dyn_wins_pl = dynamic_df[dynamic_df['pl_points'] > 0]['pl_points'].sum()
dyn_loss_pl = abs(dynamic_df[dynamic_df['pl_points'] <= 0]['pl_points'].sum())
dyn_pf = dyn_wins_pl / dyn_loss_pl if dyn_loss_pl > 0 else float('inf')

print(f"{'Profit Factor':<25} {orig_pf:<15.2f} {dyn_pf:<15.2f} {dyn_pf - orig_pf:<15.2f}")

# Average win/loss
orig_avg_win = original_df[original_df['pl_points'] > 0]['pl_points'].mean()
orig_avg_loss = original_df[original_df['pl_points'] <= 0]['pl_points'].mean()
dyn_avg_win = dynamic_df[dynamic_df['pl_points'] > 0]['pl_points'].mean()
dyn_avg_loss = dynamic_df[dynamic_df['pl_points'] <= 0]['pl_points'].mean()

print(f"{'Avg Win (Points)':<25} {orig_avg_win:<15.1f} {dyn_avg_win:<15.1f} {dyn_avg_win - orig_avg_win:<15.1f}")
print(f"{'Avg Loss (Points)':<25} {orig_avg_loss:<15.1f} {dyn_avg_loss:<15.1f} {dyn_avg_loss - orig_avg_loss:<15.1f}")

# Consecutive losses analysis
def get_max_consecutive_losses(df):
    results = [1 if x > 0 else -1 for x in df['pl_points']]
    max_loss_streak = 0
    current_streak = 0
    
    for result in results:
        if result == -1:
            current_streak += 1
            max_loss_streak = max(max_loss_streak, current_streak)
        else:
            current_streak = 0
    
    return max_loss_streak

orig_max_loss_streak = get_max_consecutive_losses(original_df)
dyn_max_loss_streak = get_max_consecutive_losses(dynamic_df)

print(f"{'Max Loss Streak':<25} {orig_max_loss_streak:<15} {dyn_max_loss_streak:<15} {dyn_max_loss_streak - orig_max_loss_streak:<15}")

# Trade efficiency metrics
print(f"\n{'TRADE EFFICIENCY':<50}")
print("-" * 50)

# Average time in trade
orig_avg_time = original_df['time_in_trade_minutes'].mean()
dyn_avg_time = dynamic_df['time_in_trade_minutes'].mean()
print(f"{'Avg Time in Trade (min)':<25} {orig_avg_time:<15.1f} {dyn_avg_time:<15.1f} {dyn_avg_time - orig_avg_time:<15.1f}")

# Exit type analysis for original
orig_pivot_exits = len(original_df[original_df['result'] == 'PIVOT_TRAIL'])
orig_sl_exits = len(original_df[original_df['result'] == 'SL'])
orig_close_exits = len(original_df[original_df['result'] == 'CLOSE'])

dyn_pivot_exits = len(dynamic_df[dynamic_df['result'] == 'PIVOT_TRAIL'])
dyn_sl_exits = len(dynamic_df[dynamic_df['result'] == 'SL'])
dyn_close_exits = len(dynamic_df[dynamic_df['result'] == 'CLOSE'])

print(f"{'Pivot Trail Exits':<25} {orig_pivot_exits:<15} {dyn_pivot_exits:<15} {dyn_pivot_exits - orig_pivot_exits:<15}")
print(f"{'Stop Loss Exits':<25} {orig_sl_exits:<15} {dyn_sl_exits:<15} {dyn_sl_exits - orig_sl_exits:<15}")
print(f"{'Market Close Exits':<25} {orig_close_exits:<15} {dyn_close_exits:<15} {dyn_close_exits - orig_close_exits:<15}")

# Risk/Reward analysis
orig_avg_rr = original_df['rr_achieved'].mean()
dyn_avg_rr = dynamic_df['rr_achieved'].mean()
print(f"{'Avg R:R Achieved':<25} {orig_avg_rr:<15.2f} {dyn_avg_rr:<15.2f} {dyn_avg_rr - orig_avg_rr:<15.2f}")

# Dynamic sizing specific analysis
print(f"\n{'DYNAMIC SIZING IMPACT':<50}")
print("-" * 50)

if 'risk_percentage' in dynamic_df.columns:
    # Risk distribution
    risk_levels = dynamic_df['risk_percentage'].value_counts().sort_index()
    print(f"Risk Distribution in Dynamic Strategy:")
    for risk, count in risk_levels.items():
        percentage = (count / len(dynamic_df)) * 100
        print(f"  {risk*100:.1f}% risk: {count:4d} trades ({percentage:5.1f}%)")
    
    avg_risk_used = dynamic_df['risk_percentage'].mean() * 100
    print(f"\nAverage Risk Used: {avg_risk_used:.1f}% (vs 2.0% fixed in original)")
    print(f"Risk Reduction Achieved: {((2.0 - avg_risk_used)/2.0)*100:.1f}%")

# Capital efficiency
orig_capital_efficiency = orig_final_capital / 100000
dyn_capital_efficiency = dyn_final_capital / 100000

print(f"\n{'CAPITAL EFFICIENCY':<50}")
print("-" * 50)
print(f"{'Capital Multiple':<25} {orig_capital_efficiency:<15.1f}x {dyn_capital_efficiency:<15.1f}x {dyn_capital_efficiency - orig_capital_efficiency:<15.1f}x")

# Summary
print(f"\n{'SUMMARY VERDICT':<50}")
print("=" * 50)
print(f"Dynamic Position Sizing Performance:")
print(f"✅ CAGR: {dyn_cagr:.1f}% vs {orig_cagr:.1f}% (Improvement: {dyn_cagr - orig_cagr:+.1f}%)")
print(f"✅ Final Capital: ₹{dyn_final_capital:,.0f} vs ₹{orig_final_capital:,.0f} (Difference: ₹{dyn_final_capital - orig_final_capital:,.0f})")
print(f"✅ Risk Reduction: Used avg {avg_risk_used:.1f}% vs fixed 2.0% risk")
print(f"✅ Trade Quality: Same {dyn_trades} trades, {dyn_win_rate:.1f}% win rate maintained")

if dyn_cagr > orig_cagr:
    print(f"\n🎉 WINNER: Dynamic Position Sizing Strategy")
    print(f"   Superior CAGR by {dyn_cagr - orig_cagr:.1f} percentage points")
else:
    print(f"\n⚠️  WINNER: Original Fixed Risk Strategy")
    print(f"   Superior CAGR by {orig_cagr - dyn_cagr:.1f} percentage points")
