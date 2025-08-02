import pandas as pd
import numpy as np

# Load both strategy results
original_df = pd.read_csv('backtest_results_pivot_trail.csv')
dynamic_df = pd.read_csv('backtest_results_pivot_trail_dynamic.csv')

print("="*80)
print("CAPITAL DRAWDOWN ANALYSIS: Original vs Dynamic Position Sizing")
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

print(f"\n{'CAPITAL DRAWDOWN COMPARISON':<50}")
print("-" * 50)
print(f"{'Metric':<35} {'Original':<15} {'Dynamic':<15} {'Difference':<15}")
print("-" * 50)
print(f"{'Max Capital DD (%)':<35} {orig_dd['max_drawdown_pct']:<15.2f} {dyn_dd['max_drawdown_pct']:<15.2f} {dyn_dd['max_drawdown_pct'] - orig_dd['max_drawdown_pct']:<15.2f}")
print(f"{'Max Capital DD (₹)':<35} {orig_dd['max_drawdown_amount']:<15,.0f} {dyn_dd['max_drawdown_amount']:<15,.0f} {dyn_dd['max_drawdown_amount'] - orig_dd['max_drawdown_amount']:<15,.0f}")

# Analyze the worst drawdown period
orig_worst_start = orig_dd['max_dd_start_idx']
orig_worst_end = orig_dd['max_dd_end_idx']
dyn_worst_start = dyn_dd['max_dd_start_idx']
dyn_worst_end = dyn_dd['max_dd_end_idx']

print(f"\n{'WORST DRAWDOWN PERIOD ANALYSIS':<50}")
print("-" * 50)
print(f"Original Strategy - Worst Drawdown:")
print(f"  Period: Trade {orig_worst_start + 1} to Trade {orig_worst_end + 1}")
print(f"  Peak Capital: ₹{orig_dd['peak_series'][orig_worst_end]:,.0f}")
print(f"  Trough Capital: ₹{original_df['exit_capital'].iloc[orig_worst_end]:,.0f}")
print(f"  Drawdown: {orig_dd['max_drawdown_pct']:.2f}% (₹{orig_dd['max_drawdown_amount']:,.0f})")

print(f"\nDynamic Strategy - Worst Drawdown:")
print(f"  Period: Trade {dyn_worst_start + 1} to Trade {dyn_worst_end + 1}")
print(f"  Peak Capital: ₹{dyn_dd['peak_series'][dyn_worst_end]:,.0f}")
print(f"  Trough Capital: ₹{dynamic_df['exit_capital'].iloc[dyn_worst_end]:,.0f}")
print(f"  Drawdown: {dyn_dd['max_drawdown_pct']:.2f}% (₹{dyn_dd['max_drawdown_amount']:,.0f})")

# Analyze position sizing impact during drawdown periods
print(f"\n{'POSITION SIZING DURING DRAWDOWNS':<50}")
print("-" * 50)

# Find periods where dynamic sizing reduced risk
reduced_risk_trades = dynamic_df[dynamic_df['risk_percentage'] < 0.02]
print(f"Trades with reduced risk: {len(reduced_risk_trades)} ({len(reduced_risk_trades)/len(dynamic_df)*100:.1f}%)")

# Calculate what the P&L would have been with full risk
reduced_risk_trades_copy = reduced_risk_trades.copy()
# Calculate what full 2% risk would have given
full_risk_pl = reduced_risk_trades_copy['pl_points'] * (0.02 / reduced_risk_trades_copy['risk_percentage'])
actual_pl = reduced_risk_trades_copy['actual_pl']

total_missed_profit = (full_risk_pl * reduced_risk_trades_copy['entry_capital'] / 100).sum() - actual_pl.sum()
print(f"Total missed profit from reduced risk: ₹{total_missed_profit:,.0f}")

# Analyze compound effect
print(f"\n{'COMPOUND EFFECT ANALYSIS':<50}")
print("-" * 50)

# Track capital differences over time
capital_diff = dynamic_df['exit_capital'] - original_df['exit_capital']
print(f"Capital difference evolution:")
print(f"  After 500 trades: ₹{capital_diff.iloc[499]:,.0f}")
print(f"  After 1000 trades: ₹{capital_diff.iloc[999]:,.0f}")
print(f"  After 1500 trades: ₹{capital_diff.iloc[1499]:,.0f}")
print(f"  After 2000 trades: ₹{capital_diff.iloc[1999]:,.0f}")
print(f"  Final difference: ₹{capital_diff.iloc[-1]:,.0f}")

# Check if dynamic sizing is actually being applied correctly
print(f"\n{'DYNAMIC SIZING VERIFICATION':<50}")
print("-" * 50)

# Compare position sizes
orig_lots = original_df['lots_traded'].values
dyn_lots = dynamic_df['lots_traded'].values

lots_diff = dyn_lots - orig_lots
trades_with_different_lots = np.sum(lots_diff != 0)
print(f"Trades with different lot sizes: {trades_with_different_lots} ({trades_with_different_lots/len(dynamic_df)*100:.1f}%)")

if trades_with_different_lots > 0:
    print(f"Average lot difference when different: {lots_diff[lots_diff != 0].mean():.2f}")
    print(f"Max lot reduction: {lots_diff.min():.0f} lots")
    print(f"Max lot increase: {lots_diff.max():.0f} lots")

# Analyze consecutive loss periods
def find_loss_streaks(df):
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
                    'end_capital': df['exit_capital'].iloc[i - 1]
                })
            current_streak = 0
    
    # Handle case where data ends in a loss streak
    if current_streak > 0:
        streaks.append({
            'length': current_streak,
            'start_idx': streak_start,
            'end_idx': len(results) - 1,
            'start_capital': df['entry_capital'].iloc[streak_start],
            'end_capital': df['exit_capital'].iloc[-1]
        })
    
    return streaks

orig_streaks = find_loss_streaks(original_df)
dyn_streaks = find_loss_streaks(dynamic_df)

# Find the longest loss streaks
orig_longest = max(orig_streaks, key=lambda x: x['length'])
dyn_longest = max(dyn_streaks, key=lambda x: x['length'])

print(f"\n{'LONGEST LOSS STREAK ANALYSIS':<50}")
print("-" * 50)
print(f"Original Strategy - Longest streak: {orig_longest['length']} losses")
print(f"  Capital at start: ₹{orig_longest['start_capital']:,.0f}")
print(f"  Capital at end: ₹{orig_longest['end_capital']:,.0f}")
print(f"  Capital lost: ₹{orig_longest['start_capital'] - orig_longest['end_capital']:,.0f}")
print(f"  Percentage lost: {(orig_longest['start_capital'] - orig_longest['end_capital'])/orig_longest['start_capital']*100:.2f}%")

print(f"\nDynamic Strategy - Longest streak: {dyn_longest['length']} losses")
print(f"  Capital at start: ₹{dyn_longest['start_capital']:,.0f}")
print(f"  Capital at end: ₹{dyn_longest['end_capital']:,.0f}")
print(f"  Capital lost: ₹{dyn_longest['start_capital'] - dyn_longest['end_capital']:,.0f}")
print(f"  Percentage lost: {(dyn_longest['start_capital'] - dyn_longest['end_capital'])/dyn_longest['start_capital']*100:.2f}%")

capital_saved = (orig_longest['start_capital'] - orig_longest['end_capital']) - (dyn_longest['start_capital'] - dyn_longest['end_capital'])
print(f"\nCapital saved during longest streak: ₹{capital_saved:,.0f}")

# Check what happens immediately after loss streaks
print(f"\n{'POST-STREAK RECOVERY ANALYSIS':<50}")
print("-" * 50)

def analyze_post_streak_recovery(df, streaks):
    recoveries = []
    for streak in streaks:
        if streak['length'] >= 5:  # Only analyze significant streaks
            post_streak_idx = streak['end_idx'] + 1
            if post_streak_idx < len(df):
                # Check next 5 trades after the streak
                recovery_window = min(5, len(df) - post_streak_idx)
                recovery_trades = df.iloc[post_streak_idx:post_streak_idx + recovery_window]
                
                recovery_info = {
                    'streak_length': streak['length'],
                    'recovery_capital_start': df['entry_capital'].iloc[post_streak_idx],
                    'recovery_trades': len(recovery_trades),
                    'recovery_pl': recovery_trades['actual_pl'].sum(),
                    'avg_lots_in_recovery': recovery_trades['lots_traded'].mean()
                }
                recoveries.append(recovery_info)
    return recoveries

orig_recoveries = analyze_post_streak_recovery(original_df, orig_streaks)
dyn_recoveries = analyze_post_streak_recovery(dynamic_df, dyn_streaks)

if orig_recoveries and dyn_recoveries:
    avg_orig_recovery = np.mean([r['recovery_pl'] for r in orig_recoveries])
    avg_dyn_recovery = np.mean([r['recovery_pl'] for r in dyn_recoveries])
    avg_orig_lots = np.mean([r['avg_lots_in_recovery'] for r in orig_recoveries])
    avg_dyn_lots = np.mean([r['avg_lots_in_recovery'] for r in dyn_recoveries])
    
    print(f"Average recovery P&L after 5+ loss streaks:")
    print(f"  Original: ₹{avg_orig_recovery:,.0f} (avg {avg_orig_lots:.1f} lots)")
    print(f"  Dynamic:  ₹{avg_dyn_recovery:,.0f} (avg {avg_dyn_lots:.1f} lots)")
    print(f"  Difference: ₹{avg_dyn_recovery - avg_orig_recovery:,.0f}")

print(f"\n{'SUMMARY INSIGHTS':<50}")
print("=" * 50)
print("Why dynamic sizing doesn't provide expected compound benefit:")
print("1. Point-based drawdowns are identical (same trade selection)")
print("2. Capital drawdowns are different but smaller than expected")
print("3. Reduced position sizes during loss streaks limit losses")
print("4. BUT: Same reduced sizes limit gains during recovery")
print("5. Net effect: Marginally lower final capital despite better risk management")
