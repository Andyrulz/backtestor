import pandas as pd
import numpy as np

# Load both strategy results
original_df = pd.read_csv('backtest_results_pivot_trail.csv')
dynamic_df = pd.read_csv('backtest_results_pivot_trail_dynamic.csv')

print("="*80)
print("CAPITAL DRAWDOWN ANALYSIS: Why Dynamic Sizing Doesn't Compound Better")
print("="*80)

# Function to calculate capital drawdowns
def calculate_capital_drawdowns(df):
    capital_curve = df['exit_capital'].values
    peak = np.maximum.accumulate(capital_curve)
    drawdown = (peak - capital_curve) / peak * 100  # Percentage drawdown
    max_dd_pct = drawdown.max()
    max_dd_amount = (peak - capital_curve).max()
    
    # Find the worst drawdown period
    max_dd_idx = drawdown.argmax()
    max_dd_peak_idx = np.where(peak == peak[max_dd_idx])[0][0]
    
    return {
        'max_drawdown_pct': max_dd_pct,
        'max_drawdown_amount': max_dd_amount,
        'drawdown_series': drawdown,
        'peak_series': peak,
        'max_dd_start_idx': max_dd_peak_idx,
        'max_dd_end_idx': max_dd_idx
    }

# Calculate capital drawdowns
orig_dd = calculate_capital_drawdowns(original_df)
dyn_dd = calculate_capital_drawdowns(dynamic_df)

print(f"\n{'🔍 CAPITAL DRAWDOWN COMPARISON':<50}")
print("-" * 70)
print(f"{'Metric':<35} {'Original':<15} {'Dynamic':<15} {'Difference':<15}")
print("-" * 70)
print(f"{'Max Capital DD (%)':<35} {orig_dd['max_drawdown_pct']:<15.2f} {dyn_dd['max_drawdown_pct']:<15.2f} {dyn_dd['max_drawdown_pct'] - orig_dd['max_drawdown_pct']:<15.2f}")
print(f"{'Max Capital DD (₹)':<35} {orig_dd['max_drawdown_amount']:<15,.0f} {dyn_dd['max_drawdown_amount']:<15,.0f} {dyn_dd['max_drawdown_amount'] - orig_dd['max_drawdown_amount']:<15,.0f}")

# Calculate position sizes to understand the mechanics
print(f"\n{'💰 POSITION SIZING MECHANICS ANALYSIS':<50}")
print("-" * 70)

# Calculate implied position sizes for both strategies
def calculate_position_size(capital, risk_pct, sl_distance):
    """Calculate position size based on capital, risk%, and SL distance"""
    risk_amount = capital * risk_pct
    return risk_amount / sl_distance if sl_distance > 0 else 0

# Add position size calculations
original_df['implied_lots'] = original_df.apply(
    lambda row: calculate_position_size(row['entry_capital'], 0.02, row['sl_distance']), axis=1
)

dynamic_df['implied_lots'] = dynamic_df.apply(
    lambda row: calculate_position_size(row['entry_capital'], row['risk_percentage'], row['sl_distance']), axis=1
)

# Compare position sizes
position_diff = dynamic_df['implied_lots'] - original_df['implied_lots']
trades_with_smaller_positions = (position_diff < 0).sum()
trades_with_larger_positions = (position_diff > 0).sum()
trades_with_same_positions = (position_diff == 0).sum()

print(f"Position size comparison:")
print(f"  Trades with smaller positions: {trades_with_smaller_positions:4d} ({trades_with_smaller_positions/len(dynamic_df)*100:5.1f}%)")
print(f"  Trades with same positions:    {trades_with_same_positions:4d} ({trades_with_same_positions/len(dynamic_df)*100:5.1f}%)")
print(f"  Trades with larger positions:  {trades_with_larger_positions:4d} ({trades_with_larger_positions/len(dynamic_df)*100:5.1f}%)")

avg_position_reduction = position_diff[position_diff < 0].mean()
max_position_reduction = position_diff.min()
print(f"\nAverage position reduction when smaller: {avg_position_reduction:.2f} lots")
print(f"Maximum position reduction: {max_position_reduction:.2f} lots")

# Analyze the impact during winning vs losing trades
winning_trades_dyn = dynamic_df[dynamic_df['pl_points'] > 0]
losing_trades_dyn = dynamic_df[dynamic_df['pl_points'] <= 0]

winning_reduced_risk = winning_trades_dyn[winning_trades_dyn['risk_percentage'] < 0.02]
losing_reduced_risk = losing_trades_dyn[losing_trades_dyn['risk_percentage'] < 0.02]

print(f"\n{'📊 IMPACT ON WINNING vs LOSING TRADES':<50}")
print("-" * 70)
print(f"Winning trades with reduced risk: {len(winning_reduced_risk):4d} ({len(winning_reduced_risk)/len(winning_trades_dyn)*100:5.1f}% of wins)")
print(f"Losing trades with reduced risk:  {len(losing_reduced_risk):4d} ({len(losing_reduced_risk)/len(losing_trades_dyn)*100:5.1f}% of losses)")

# Calculate missed profit from winning trades with reduced risk
if len(winning_reduced_risk) > 0:
    # What would the P&L have been with full 2% risk
    full_risk_pl = winning_reduced_risk['pl_points'] * (0.02 / winning_reduced_risk['risk_percentage'])
    actual_pl = winning_reduced_risk['pl_points']
    
    # Calculate monetary impact
    missed_profit_per_trade = (full_risk_pl - actual_pl) * winning_reduced_risk['entry_capital'] / 100
    total_missed_profit = missed_profit_per_trade.sum()
    
    print(f"\nMissed profit from winning trades with reduced risk:")
    print(f"  Total missed profit: ₹{total_missed_profit:,.0f}")
    print(f"  Average per affected winning trade: ₹{total_missed_profit/len(winning_reduced_risk):,.0f}")

# Calculate saved losses from losing trades with reduced risk
if len(losing_reduced_risk) > 0:
    # What would the loss have been with full 2% risk
    full_risk_loss = losing_reduced_risk['pl_points'] * (0.02 / losing_reduced_risk['risk_percentage'])
    actual_loss = losing_reduced_risk['pl_points']
    
    # Calculate monetary impact (saved losses)
    saved_loss_per_trade = (actual_loss - full_risk_loss) * losing_reduced_risk['entry_capital'] / 100
    total_saved_losses = saved_loss_per_trade.sum()
    
    print(f"\nSaved losses from losing trades with reduced risk:")
    print(f"  Total saved losses: ₹{total_saved_losses:,.0f}")
    print(f"  Average per affected losing trade: ₹{total_saved_losses/len(losing_reduced_risk):,.0f}")

# Net impact calculation
net_impact = total_saved_losses - total_missed_profit
print(f"\nNet impact of dynamic sizing: ₹{net_impact:,.0f}")
print(f"(Positive = beneficial, Negative = detrimental)")

# Analyze consecutive loss periods and their impact
print(f"\n{'📉 CONSECUTIVE LOSS ANALYSIS':<50}")
print("-" * 70)

def analyze_loss_streaks(df):
    results = [1 if x > 0 else -1 for x in df['pl_points']]
    streaks = []
    current_streak = 0
    streak_start = 0
    
    for i, result in enumerate(results):
        if result == -1:
            if current_streak == 0:
                streak_start = i
            current_streak += 1
        else:
            if current_streak > 0:
                streaks.append({
                    'length': current_streak,
                    'start_idx': streak_start,
                    'end_idx': i - 1,
                    'start_capital': df['entry_capital'].iloc[streak_start],
                    'end_capital': df['exit_capital'].iloc[i - 1],
                    'total_loss': df['actual_pl'].iloc[streak_start:i].sum()
                })
            current_streak = 0
    
    return [s for s in streaks if s['length'] >= 5]  # Only significant streaks

orig_streaks = analyze_loss_streaks(original_df)
dyn_streaks = analyze_loss_streaks(dynamic_df)

print(f"Loss streaks of 5+ trades:")
print(f"  Original strategy: {len(orig_streaks)} streaks")
print(f"  Dynamic strategy:  {len(dyn_streaks)} streaks")

if orig_streaks and dyn_streaks:
    # Compare the longest streaks
    orig_longest = max(orig_streaks, key=lambda x: x['length'])
    dyn_longest = max(dyn_streaks, key=lambda x: x['length'])
    
    print(f"\nLongest loss streak comparison:")
    print(f"  Original: {orig_longest['length']} losses, ₹{abs(orig_longest['total_loss']):,.0f} lost")
    print(f"  Dynamic:  {dyn_longest['length']} losses, ₹{abs(dyn_longest['total_loss']):,.0f} lost")
    print(f"  Capital saved: ₹{abs(orig_longest['total_loss']) - abs(dyn_longest['total_loss']):,.0f}")

# WHY THE COMPOUND EFFECT DOESN'T WORK AS EXPECTED
print(f"\n{'🧠 WHY COMPOUND EFFECT IS LIMITED':<50}")
print("=" * 70)

print("KEY INSIGHTS:")
print("1. IDENTICAL TRADE SELECTION: Both strategies take exactly the same trades")
print("   → No advantage in avoiding bad periods or catching good periods")
print()
print("2. SYMMETRIC IMPACT: Dynamic sizing affects BOTH wins and losses")
print("   → Reduces losses during bad streaks ✅")
print("   → But also reduces gains during recoveries ❌")
print()
print("3. TIMING MISMATCH: Risk reduction happens DURING loss streaks")
print("   → Protection is active when you're already losing")
print("   → But stays active during early recovery (missing upside)")
print()
print("4. RESET MECHANISM: Only resets after 1 win")
print("   → Single win doesn't guarantee end of difficult period")
print("   → May reduce risk again quickly if next trade loses")
print()

# Calculate the capital trajectory difference
capital_diff_evolution = dynamic_df['exit_capital'] - original_df['exit_capital']

print("5. CUMULATIVE IMPACT: Capital difference grows over time")
checkpoints = [500, 1000, 1500, 2000, len(dynamic_df)-1]
for cp in checkpoints:
    if cp < len(capital_diff_evolution):
        print(f"   After {cp+1:4d} trades: ₹{capital_diff_evolution.iloc[cp]:>10,.0f}")

print()
print("CONCLUSION: Dynamic sizing provides psychological comfort and risk")
print("management but at the cost of absolute performance due to the")
print("symmetric impact on both wins and losses.")
