import pandas as pd
import numpy as np
from datetime import datetime, time

# Load both strategy results
original_df = pd.read_csv('backtest_results_pivot_trail.csv')
dynamic_df = pd.read_csv('backtest_results_pivot_trail_dynamic.csv')

print("="*80)
print("BIG WINNERS & LOSERS ANALYSIS: Pattern Recognition for Smart Position Sizing")
print("="*80)

# Use original data for pattern analysis (same trades, cleaner to analyze)
df = original_df.copy()

# Convert time columns
df['entry_time'] = pd.to_datetime(df['entry_time'])
df['exit_time'] = pd.to_datetime(df['exit_time'])
df['breakout_time'] = pd.to_datetime(df['breakout_time'])

# Add time-based features
df['entry_hour'] = df['entry_time'].dt.hour
df['entry_minute'] = df['entry_time'].dt.minute
df['entry_day_of_week'] = df['entry_time'].dt.dayofweek  # 0 = Monday
df['entry_month'] = df['entry_time'].dt.month

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

# Analyze patterns for big winners
print(f"\n{'🏆 BIG WINNERS PATTERN ANALYSIS':<60}")
print("-" * 70)

def analyze_pattern(group, label):
    print(f"\n{label} Characteristics:")
    print(f"  Average P&L: {group['pl_points'].mean():.1f} points")
    print(f"  Average time in trade: {group['time_in_trade_minutes'].mean():.1f} minutes")
    print(f"  Average SL distance: {group['sl_distance'].mean():.1f} points")
    print(f"  Average R:R achieved: {group['rr_achieved'].mean():.2f}")
    print(f"  Max favorable move: {group['max_favorable'].mean():.1f} points")
    print(f"  Max adverse move: {group['max_adverse'].mean():.1f} points")
    
    # Direction analysis
    direction_counts = group['direction'].value_counts()
    print(f"  Direction bias:")
    for direction, count in direction_counts.items():
        pct = (count / len(group)) * 100
        print(f"    {direction}: {count} trades ({pct:.1f}%)")
    
    # Exit type analysis
    exit_counts = group['result'].value_counts()
    print(f"  Exit types:")
    for exit_type, count in exit_counts.items():
        pct = (count / len(group)) * 100
        print(f"    {exit_type}: {count} trades ({pct:.1f}%)")
    
    # Time analysis
    print(f"  Entry time patterns:")
    print(f"    Most common hour: {group['entry_hour'].mode().iloc[0] if len(group['entry_hour'].mode()) > 0 else 'N/A'}")
    print(f"    Average entry hour: {group['entry_hour'].mean():.1f}")
    
    # Day of week analysis
    dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    dow_counts = group['entry_day_of_week'].value_counts().sort_index()
    print(f"  Day of week distribution:")
    for dow, count in dow_counts.items():
        if dow < 5:  # Only weekdays
            pct = (count / len(group)) * 100
            print(f"    {dow_names[dow]}: {count} trades ({pct:.1f}%)")
    
    return group

big_winners_analyzed = analyze_pattern(big_winners, "BIG WINNERS")

print(f"\n{'💀 BIG LOSERS PATTERN ANALYSIS':<60}")
print("-" * 70)

big_losers_analyzed = analyze_pattern(big_losers, "BIG LOSERS")

# Compare patterns between winners and losers
print(f"\n{'⚖️ COMPARATIVE PATTERN ANALYSIS':<60}")
print("-" * 70)

def compare_patterns(winners, losers, feature, label):
    winner_avg = winners[feature].mean()
    loser_avg = losers[feature].mean()
    difference = winner_avg - loser_avg
    print(f"{label}:")
    print(f"  Winners: {winner_avg:.2f}")
    print(f"  Losers:  {loser_avg:.2f}")
    print(f"  Difference: {difference:+.2f}")
    return difference

print("Key differences between big winners and losers:")
sl_diff = compare_patterns(big_winners, big_losers, 'sl_distance', 'SL Distance (points)')
time_diff = compare_patterns(big_winners, big_losers, 'time_in_trade_minutes', 'Time in Trade (minutes)')
fav_diff = compare_patterns(big_winners, big_losers, 'max_favorable', 'Max Favorable Move (points)')
adv_diff = compare_patterns(big_winners, big_losers, 'max_adverse', 'Max Adverse Move (points)')

# Analyze volatility patterns
print(f"\n{'📊 VOLATILITY & MARKET CONDITIONS':<60}")
print("-" * 70)

# Calculate daily volatility proxy using pivot level spreads
df['pivot_volatility'] = df['pivot_level'].rolling(window=50).std()

winner_vol = big_winners['pivot_volatility'].mean()
loser_vol = big_losers['pivot_volatility'].mean()
print(f"Market volatility during trades:")
print(f"  Big winners avg volatility: {winner_vol:.2f}")
print(f"  Big losers avg volatility: {loser_vol:.2f}")
print(f"  Difference: {winner_vol - loser_vol:+.2f}")

# Analyze marking candle updates (strategy complexity indicator)
winner_marking = big_winners['marking_updates'].mean()
loser_marking = big_losers['marking_updates'].mean()
print(f"\nMarking candle complexity:")
print(f"  Big winners avg updates: {winner_marking:.1f}")
print(f"  Big losers avg updates: {loser_marking:.1f}")
print(f"  Difference: {winner_marking - loser_marking:+.1f}")

# Time-based analysis for optimal entry timing
print(f"\n{'⏰ OPTIMAL TIMING ANALYSIS':<60}")
print("-" * 70)

# Analyze performance by hour
hourly_performance = df.groupby('entry_hour').agg({
    'pl_points': ['mean', 'count', 'sum'],
    'rr_achieved': 'mean'
}).round(2)

hourly_performance.columns = ['Avg_PL', 'Trade_Count', 'Total_PL', 'Avg_RR']
print("Performance by entry hour:")
print(hourly_performance.to_string())

# Find best and worst hours
best_hours = hourly_performance[hourly_performance['Trade_Count'] >= 20].nlargest(3, 'Avg_PL')
worst_hours = hourly_performance[hourly_performance['Trade_Count'] >= 20].nsmallest(3, 'Avg_PL')

print(f"\nBest performing hours (min 20 trades):")
for hour in best_hours.index:
    print(f"  {hour:02d}:00 - Avg P&L: {best_hours.loc[hour, 'Avg_PL']:.1f} points ({best_hours.loc[hour, 'Trade_Count']} trades)")

print(f"\nWorst performing hours (min 20 trades):")
for hour in worst_hours.index:
    print(f"  {hour:02d}:00 - Avg P&L: {worst_hours.loc[hour, 'Avg_PL']:.1f} points ({worst_hours.loc[hour, 'Trade_Count']} trades)")

# Analyze R:R achievement patterns
print(f"\n{'🎯 RISK-REWARD ACHIEVEMENT PATTERNS':<60}")
print("-" * 70)

# Categorize trades by R:R achieved
df['rr_category'] = pd.cut(df['rr_achieved'], 
                          bins=[-float('inf'), -1, 0, 0.5, 1, 2, float('inf')],
                          labels=['Heavy_Loss', 'Loss', 'Small_Win', 'Good_Win', 'Great_Win', 'Exceptional'])

rr_analysis = df.groupby('rr_category').agg({
    'pl_points': ['mean', 'count', 'sum'],
    'time_in_trade_minutes': 'mean',
    'sl_distance': 'mean'
}).round(2)

print("Performance by R:R category:")
print(rr_analysis.to_string())

# Identify high-probability setups
print(f"\n{'🔍 HIGH-PROBABILITY SETUP IDENTIFICATION':<60}")
print("-" * 70)

# Define filters for potentially high-probability trades
def analyze_filter(df, filter_condition, filter_name):
    filtered_trades = df[filter_condition]
    if len(filtered_trades) > 10:  # Minimum sample size
        win_rate = (filtered_trades['pl_points'] > 0).mean() * 100
        avg_pl = filtered_trades['pl_points'].mean()
        avg_rr = filtered_trades['rr_achieved'].mean()
        trade_count = len(filtered_trades)
        
        print(f"{filter_name}:")
        print(f"  Trades: {trade_count} ({trade_count/len(df)*100:.1f}% of total)")
        print(f"  Win rate: {win_rate:.1f}%")
        print(f"  Avg P&L: {avg_pl:.1f} points")
        print(f"  Avg R:R: {avg_rr:.2f}")
        print(f"  Score: {win_rate * avg_rr:.1f} (win_rate × avg_rr)")
        print()
        
        return {
            'name': filter_name,
            'trades': trade_count,
            'win_rate': win_rate,
            'avg_pl': avg_pl,
            'avg_rr': avg_rr,
            'score': win_rate * avg_rr
        }
    return None

# Test various filters
filters_to_test = []

# Time-based filters
filters_to_test.append(analyze_filter(df, 
    (df['entry_hour'].isin([10, 11, 14, 15])), 
    "High-volume hours (10-11, 14-15)"))

filters_to_test.append(analyze_filter(df, 
    (df['entry_hour'].isin([9, 15])), 
    "Market open/close hours"))

# SL distance filters
sl_median = df['sl_distance'].median()
filters_to_test.append(analyze_filter(df, 
    (df['sl_distance'] <= sl_median), 
    "Tight SL setups (<= median SL)"))

filters_to_test.append(analyze_filter(df, 
    (df['sl_distance'] > sl_median * 1.5), 
    "Wide SL setups (> 1.5× median SL)"))

# Direction bias
filters_to_test.append(analyze_filter(df, 
    (df['direction'] == 'LONG'), 
    "Long trades only"))

filters_to_test.append(analyze_filter(df, 
    (df['direction'] == 'SHORT'), 
    "Short trades only"))

# Volatility filters
vol_median = df['pivot_volatility'].median()
filters_to_test.append(analyze_filter(df, 
    (df['pivot_volatility'] <= vol_median), 
    "Low volatility periods"))

filters_to_test.append(analyze_filter(df, 
    (df['pivot_volatility'] > vol_median), 
    "High volatility periods"))

# Combined high-probability filter
best_hours_list = best_hours.index.tolist()
combined_filter = (
    (df['entry_hour'].isin(best_hours_list)) &
    (df['sl_distance'] <= sl_median) &
    (df['pivot_volatility'] <= vol_median)
)
filters_to_test.append(analyze_filter(df, combined_filter, "Combined high-prob filter"))

# Rank filters by score
valid_filters = [f for f in filters_to_test if f is not None]
valid_filters.sort(key=lambda x: x['score'], reverse=True)

print(f"{'📈 RECOMMENDED POSITION SIZING RULES':<60}")
print("=" * 70)

print("Based on pattern analysis, consider these dynamic sizing rules:\n")

print("🔥 INCREASE POSITION SIZE (1.5× to 2× normal) for:")
top_3_filters = valid_filters[:3]
for i, f in enumerate(top_3_filters, 1):
    print(f"{i}. {f['name']}")
    print(f"   Win Rate: {f['win_rate']:.1f}%, Avg R:R: {f['avg_rr']:.2f}, Score: {f['score']:.1f}")

print(f"\n💀 REDUCE POSITION SIZE (0.5× to 0.75× normal) for:")
# Show characteristics that correlate with big losers
print("1. Wide SL setups (> 1.5× median SL distance)")
print("   Often lead to bigger losses, reduce size to limit damage")
print("2. High volatility periods") 
print("   More unpredictable price action, use smaller positions")
print("3. Late day trades after 15:00")
print("   Often whipsaws and false breakouts")

print(f"\n🛠️ IMPLEMENTATION SUGGESTIONS:")
print("-" * 40)
print("1. Base Risk: 2.0% (current system)")
print("2. High-Probability Multiplier: 1.5× to 2.0× (3.0-4.0% risk)")
print("3. Low-Probability Reducer: 0.5× to 0.75× (1.0-1.5% risk)")
print("4. Keep current consecutive loss protection as override")
print("5. Track performance by setup type for continuous optimization")

# Calculate potential impact
print(f"\n{'💰 POTENTIAL IMPACT CALCULATION':<60}")
print("-" * 70)

# Simulate smart sizing on historical data
df['smart_multiplier'] = 1.0  # Default

# Apply multipliers based on top patterns
if len(valid_filters) > 0:
    top_filter = valid_filters[0]
    # Find the condition for top filter (simplified)
    if 'High-volume' in top_filter['name']:
        high_prob_mask = df['entry_hour'].isin([10, 11, 14, 15])
    elif 'Tight SL' in top_filter['name']:
        high_prob_mask = df['sl_distance'] <= sl_median
    else:
        high_prob_mask = df['entry_hour'].isin(best_hours_list)
    
    df.loc[high_prob_mask, 'smart_multiplier'] = 1.5
    
    # Reduce for wide SL
    df.loc[df['sl_distance'] > sl_median * 1.5, 'smart_multiplier'] = 0.75

# Calculate simulated P&L with smart sizing
df['smart_pl'] = df['pl_points'] * df['smart_multiplier']
original_total_pl = df['pl_points'].sum()
smart_total_pl = df['smart_pl'].sum()
improvement = smart_total_pl - original_total_pl

print(f"Smart sizing simulation:")
print(f"  Original total P&L: {original_total_pl:.1f} points")
print(f"  Smart sizing P&L: {smart_total_pl:.1f} points")
print(f"  Improvement: {improvement:+.1f} points ({improvement/original_total_pl*100:+.1f}%)")

trades_increased = (df['smart_multiplier'] > 1.0).sum()
trades_decreased = (df['smart_multiplier'] < 1.0).sum()
print(f"  Trades with increased size: {trades_increased} ({trades_increased/len(df)*100:.1f}%)")
print(f"  Trades with decreased size: {trades_decreased} ({trades_decreased/len(df)*100:.1f}%)")
