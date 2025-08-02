import pandas as pd
import numpy as np
from datetime import datetime, time

# Load original strategy results for pattern analysis
df = pd.read_csv('backtest_results_pivot_trail.csv')

print("="*80)
print("BIG WINNERS & LOSERS ANALYSIS: Smart Position Sizing Patterns")
print("="*80)

# Convert time columns
df['entry_time'] = pd.to_datetime(df['entry_time'])
df['exit_time'] = pd.to_datetime(df['exit_time'])
df['breakout_time'] = pd.to_datetime(df['breakout_time'])

# Add time-based features
df['entry_hour'] = df['entry_time'].dt.hour
df['entry_minute'] = df['entry_time'].dt.minute
df['entry_day_of_week'] = df['entry_time'].dt.dayofweek  # 0 = Monday

# Define big winners and losers (top/bottom 10% by P&L points)
pl_90th = df['pl_points'].quantile(0.9)
pl_10th = df['pl_points'].quantile(0.1)

big_winners = df[df['pl_points'] >= pl_90th].copy()
big_losers = df[df['pl_points'] <= pl_10th].copy()

print(f"\n{'🎯 BIG WINNERS & LOSERS OVERVIEW':<60}")
print("-" * 70)
print(f"Total trades analyzed: {len(df):,}")
print(f"Big winners (top 10%): {len(big_winners):,} trades (P&L >= {pl_90th:.1f} points)")
print(f"Big losers (bottom 10%): {len(big_losers):,} trades (P&L <= {pl_10th:.1f} points)")
print(f"Winner P&L range: {big_winners['pl_points'].min():.1f} to {big_winners['pl_points'].max():.1f} points")
print(f"Loser P&L range: {big_losers['pl_points'].min():.1f} to {big_losers['pl_points'].max():.1f} points")

# KEY INSIGHTS FROM INITIAL OUTPUT
print(f"\n{'🔍 CRITICAL PATTERN INSIGHTS':<60}")
print("=" * 70)

print("🏆 BIG WINNERS characteristics:")
print(f"  • Average SL distance: 8.5 points (TIGHT setups)")
print(f"  • Average time in trade: 126 minutes (LONG holds)")
print(f"  • 73.8% exit via PIVOT_TRAIL (trend following works)")
print(f"  • 60% LONG bias (market uptrend preference)")
print(f"  • R:R achieved: 9.5× (massive winners)")
print(f"  • Max adverse: 2.4 points (minimal drawdown)")

print(f"\n💀 BIG LOSERS characteristics:")
print(f"  • Average SL distance: 14.4 points (WIDE setups)")
print(f"  • Average time in trade: 9 minutes (QUICK stops)")
print(f"  • 97.1% exit via STOP LOSS (immediate failure)")
print(f"  • 53.5% SHORT bias (shorts fail more often)")
print(f"  • Max adverse: 7.3 points (immediate pain)")

print(f"\n{'⚡ KEY DIFFERENTIATORS':<60}")
print("-" * 70)
print(f"1. SL DISTANCE: Winners use 8.5pt vs Losers use 14.4pt (41% tighter)")
print(f"2. HOLD TIME: Winners hold 126min vs Losers 9min (14× longer)")
print(f"3. EXIT TYPE: Winners trail 74% vs Losers hit SL 97%")
print(f"4. DIRECTION: Winners favor LONG, Losers favor SHORT")

# Detailed analysis of SL distance patterns
print(f"\n{'📏 STOP LOSS DISTANCE ANALYSIS':<60}")
print("-" * 70)

sl_bins = [0, 7, 10, 15, 20, float('inf')]
sl_labels = ['Tight (≤7)', 'Medium (7-10)', 'Wide (10-15)', 'Very Wide (15-20)', 'Extreme (>20)']
df['sl_category'] = pd.cut(df['sl_distance'], bins=sl_bins, labels=sl_labels, include_lowest=True)

sl_analysis = df.groupby('sl_category').agg({
    'pl_points': ['mean', 'count'],
    'rr_achieved': 'mean'
}).round(2)

sl_analysis.columns = ['Avg_PL', 'Count', 'Avg_RR']
win_rates = df.groupby('sl_category')['pl_points'].apply(lambda x: (x > 0).mean() * 100).round(1)
sl_analysis['Win_Rate'] = win_rates

print("Performance by SL distance category:")
print(sl_analysis.to_string())

# Time analysis
print(f"\n{'⏰ TIMING ANALYSIS':<60}")
print("-" * 70)

hourly_stats = df.groupby('entry_hour').agg({
    'pl_points': ['mean', 'count'],
    'rr_achieved': 'mean'
}).round(2)

hourly_stats.columns = ['Avg_PL', 'Count', 'Avg_RR']
hourly_win_rates = df.groupby('entry_hour')['pl_points'].apply(lambda x: (x > 0).mean() * 100).round(1)
hourly_stats['Win_Rate'] = hourly_win_rates

# Only show hours with reasonable sample size
significant_hours = hourly_stats[hourly_stats['Count'] >= 20]
print("Performance by entry hour (min 20 trades):")
print(significant_hours.to_string())

best_hours = significant_hours.nlargest(3, 'Avg_PL')
worst_hours = significant_hours.nsmallest(3, 'Avg_PL')

print(f"\n🔥 BEST performing hours:")
for hour in best_hours.index:
    stats = best_hours.loc[hour]
    print(f"  {hour:02d}:00 - Avg: {stats['Avg_PL']:>6.1f}pts, Win Rate: {stats['Win_Rate']:>5.1f}%, R:R: {stats['Avg_RR']:>4.2f}")

print(f"\n💀 WORST performing hours:")
for hour in worst_hours.index:
    stats = worst_hours.loc[hour]
    print(f"  {hour:02d}:00 - Avg: {stats['Avg_PL']:>6.1f}pts, Win Rate: {stats['Win_Rate']:>5.1f}%, R:R: {stats['Avg_RR']:>4.2f}")

# Direction analysis
print(f"\n{'↗️ DIRECTION BIAS ANALYSIS':<60}")
print("-" * 70)

direction_stats = df.groupby('direction').agg({
    'pl_points': ['mean', 'count', 'sum'],
    'rr_achieved': 'mean'
}).round(2)

direction_stats.columns = ['Avg_PL', 'Count', 'Total_PL', 'Avg_RR']
direction_win_rates = df.groupby('direction')['pl_points'].apply(lambda x: (x > 0).mean() * 100).round(1)
direction_stats['Win_Rate'] = direction_win_rates

print("Performance by direction:")
print(direction_stats.to_string())

# Exit type analysis
print(f"\n{'🚪 EXIT TYPE ANALYSIS':<60}")
print("-" * 70)

exit_stats = df.groupby('result').agg({
    'pl_points': ['mean', 'count'],
    'time_in_trade_minutes': 'mean',
    'rr_achieved': 'mean'
}).round(2)

exit_stats.columns = ['Avg_PL', 'Count', 'Avg_Time', 'Avg_RR']
print("Performance by exit type:")
print(exit_stats.to_string())

# SMART POSITION SIZING RECOMMENDATIONS
print(f"\n{'🧠 SMART POSITION SIZING RECOMMENDATIONS':<60}")
print("=" * 70)

print("💰 INCREASE POSITION SIZE (1.5× to 2.0×) for HIGH-PROBABILITY setups:")
print("1. TIGHT SL setups (≤7 points):")
tight_sl_trades = df[df['sl_distance'] <= 7]
if len(tight_sl_trades) > 0:
    tight_win_rate = (tight_sl_trades['pl_points'] > 0).mean() * 100
    tight_avg_pl = tight_sl_trades['pl_points'].mean()
    tight_avg_rr = tight_sl_trades['rr_achieved'].mean()
    print(f"   • {len(tight_sl_trades)} trades ({len(tight_sl_trades)/len(df)*100:.1f}% of total)")
    print(f"   • Win rate: {tight_win_rate:.1f}% | Avg P&L: {tight_avg_pl:.1f}pts | Avg R:R: {tight_avg_rr:.2f}")

print(f"\n2. BEST TIMING (peak performance hours):")
if len(best_hours) > 0:
    best_hour_trades = df[df['entry_hour'].isin(best_hours.index)]
    best_time_win_rate = (best_hour_trades['pl_points'] > 0).mean() * 100
    best_time_avg_pl = best_hour_trades['pl_points'].mean()
    print(f"   • Hours {list(best_hours.index)} combined:")
    print(f"   • {len(best_hour_trades)} trades ({len(best_hour_trades)/len(df)*100:.1f}% of total)")
    print(f"   • Win rate: {best_time_win_rate:.1f}% | Avg P&L: {best_time_avg_pl:.1f}pts")

print(f"\n3. LONG BIAS (better performance than shorts):")
long_trades = df[df['direction'] == 'long']
if len(long_trades) > 0:
    long_win_rate = (long_trades['pl_points'] > 0).mean() * 100
    long_avg_pl = long_trades['pl_points'].mean()
    print(f"   • {len(long_trades)} trades ({len(long_trades)/len(df)*100:.1f}% of total)")
    print(f"   • Win rate: {long_win_rate:.1f}% | Avg P&L: {long_avg_pl:.1f}pts")

print(f"\n⚠️  REDUCE POSITION SIZE (0.5× to 0.75×) for LOW-PROBABILITY setups:")
print("1. WIDE SL setups (>15 points):")
wide_sl_trades = df[df['sl_distance'] > 15]
if len(wide_sl_trades) > 0:
    wide_win_rate = (wide_sl_trades['pl_points'] > 0).mean() * 100
    wide_avg_pl = wide_sl_trades['pl_points'].mean()
    print(f"   • {len(wide_sl_trades)} trades ({len(wide_sl_trades)/len(df)*100:.1f}% of total)")
    print(f"   • Win rate: {wide_win_rate:.1f}% | Avg P&L: {wide_avg_pl:.1f}pts")

print(f"\n2. WORST TIMING (poor performance hours):")
if len(worst_hours) > 0:
    worst_hour_trades = df[df['entry_hour'].isin(worst_hours.index)]
    worst_time_win_rate = (worst_hour_trades['pl_points'] > 0).mean() * 100
    worst_time_avg_pl = worst_hour_trades['pl_points'].mean()
    print(f"   • Hours {list(worst_hours.index)} combined:")
    print(f"   • {len(worst_hour_trades)} trades ({len(worst_hour_trades)/len(df)*100:.1f}% of total)")
    print(f"   • Win rate: {worst_time_win_rate:.1f}% | Avg P&L: {worst_time_avg_pl:.1f}pts")

# SIMULATION OF SMART SIZING
print(f"\n{'💡 SMART SIZING SIMULATION':<60}")
print("=" * 70)

# Apply smart multipliers
df['smart_multiplier'] = 1.0  # Base size

# Increase size for high-probability setups
df.loc[df['sl_distance'] <= 7, 'smart_multiplier'] = 1.75
df.loc[df['entry_hour'].isin(best_hours.index), 'smart_multiplier'] *= 1.25
df.loc[df['direction'] == 'long', 'smart_multiplier'] *= 1.1

# Reduce size for low-probability setups
df.loc[df['sl_distance'] > 15, 'smart_multiplier'] *= 0.6
df.loc[df['entry_hour'].isin(worst_hours.index), 'smart_multiplier'] *= 0.8

# Cap multipliers
df['smart_multiplier'] = df['smart_multiplier'].clip(0.3, 3.0)

# Calculate impact
df['smart_pl'] = df['pl_points'] * df['smart_multiplier']
original_pl = df['pl_points'].sum()
smart_pl = df['smart_pl'].sum()
improvement = smart_pl - original_pl

print(f"Smart sizing results:")
print(f"  Original total P&L: {original_pl:,.1f} points")
print(f"  Smart sizing P&L:   {smart_pl:,.1f} points")
print(f"  Improvement: {improvement:+,.1f} points ({improvement/original_pl*100:+.1f}%)")

size_distribution = df['smart_multiplier'].value_counts().sort_index()
print(f"\nPosition size distribution:")
for multiplier in sorted(size_distribution.index):
    count = size_distribution[multiplier]
    pct = count / len(df) * 100
    if multiplier != 1.0:
        print(f"  {multiplier:.2f}× size: {count:4d} trades ({pct:5.1f}%)")

# Detailed breakdown by category
increased_trades = df[df['smart_multiplier'] > 1.1]
decreased_trades = df[df['smart_multiplier'] < 0.9]

print(f"\nDetailed impact:")
print(f"  Increased size trades: {len(increased_trades):4d} ({len(increased_trades)/len(df)*100:5.1f}%)")
if len(increased_trades) > 0:
    inc_original = increased_trades['pl_points'].sum()
    inc_smart = increased_trades['smart_pl'].sum()
    print(f"    Original P&L: {inc_original:8.1f} → Smart P&L: {inc_smart:8.1f} ({inc_smart-inc_original:+.1f})")

print(f"  Decreased size trades: {len(decreased_trades):4d} ({len(decreased_trades)/len(df)*100:5.1f}%)")
if len(decreased_trades) > 0:
    dec_original = decreased_trades['pl_points'].sum()
    dec_smart = decreased_trades['smart_pl'].sum()
    print(f"    Original P&L: {dec_original:8.1f} → Smart P&L: {dec_smart:8.1f} ({dec_smart-dec_original:+.1f})")

print(f"\n{'🎯 FINAL RECOMMENDATIONS':<60}")
print("=" * 70)
print("Implement a 3-tier smart position sizing system:")
print("1. 🔥 HIGH-CONFIDENCE (1.5-2.0× size): Tight SL ≤7pts + Best hours + Long bias")
print("2. 📊 NORMAL (1.0× size): Standard setups")
print("3. ⚠️  LOW-CONFIDENCE (0.5-0.75× size): Wide SL >15pts + Worst hours")
print("4. Keep consecutive loss protection as additional overlay")
print(f"5. Potential improvement: +{improvement/original_pl*100:.1f}% in total P&L")
