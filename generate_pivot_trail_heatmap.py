import pandas as pd
import numpy as np

# Load the pivot trail results
df = pd.read_csv('backtest_results_pivot_trail.csv')

# Convert entry_time to datetime and extract year and month
df['entry_time'] = pd.to_datetime(df['entry_time'])
df['year'] = df['entry_time'].dt.year
df['month'] = df['entry_time'].dt.month

# Group by year and month to get monthly P&L
monthly_pl = df.groupby(['year', 'month'])['pl_points'].sum().reset_index()

# Create a pivot table for the heatmap
heatmap_data = monthly_pl.pivot(index='year', columns='month', values='pl_points').fillna(0)

# Month names for display
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

print("=" * 100)
print("MONTHLY P&L HEATMAP (Points) - PIVOT TRAIL STRATEGY")
print("=" * 100)

# Header
print(f"{'Year':<6}", end='')
for month in months:
    print(f"{month:>8}", end='')
print(f"{'Total':>10}")
print("-" * 100)

# Data rows
for year in sorted(heatmap_data.index):
    print(f"{year:<6}", end='')
    year_total = 0
    for month_num in range(1, 13):
        if month_num in heatmap_data.columns:
            month_pl = heatmap_data.loc[year, month_num] if month_num in heatmap_data.loc[year].index else 0
        else:
            month_pl = 0
        year_total += month_pl
        print(f"{month_pl:>8.1f}", end='')
    print(f"{year_total:>10.1f}")

print("=" * 100)

# Calculate monthly totals across all years
print(f"{'Total':<6}", end='')
grand_total = 0
for month_num in range(1, 13):
    if month_num in heatmap_data.columns:
        month_total = heatmap_data[month_num].sum()
    else:
        month_total = 0
    grand_total += month_total
    print(f"{month_total:>8.1f}", end='')
print(f"{grand_total:>10.1f}")
print("=" * 100)

# Additional statistics
print(f"\nPIVOT TRAIL STRATEGY - MONTHLY PERFORMANCE STATISTICS")
print("=" * 60)
print(f"Total Trades: {len(df):,}")
print(f"Total P&L: {df['pl_points'].sum():.1f} points")
print(f"Best Month: {heatmap_data.max().max():.1f} points")
print(f"Worst Month: {heatmap_data.min().min():.1f} points")
print(f"Average Monthly P&L: {df.groupby(['year', 'month'])['pl_points'].sum().mean():.1f} points")
print(f"Monthly Win Rate: {(df.groupby(['year', 'month'])['pl_points'].sum() > 0).mean() * 100:.1f}%")

# Best and worst performing months
monthly_totals = df.groupby(['year', 'month'])['pl_points'].sum()
best_month = monthly_totals.idxmax()
worst_month = monthly_totals.idxmin()

print(f"\nBest Month: {months[best_month[1]-1]} {best_month[0]} (+{monthly_totals[best_month]:.1f} pts)")
print(f"Worst Month: {months[worst_month[1]-1]} {worst_month[0]} ({monthly_totals[worst_month]:.1f} pts)")

# Consecutive Wins/Losses Analysis
print(f"\n{'='*80}")
print("CONSECUTIVE WINS & LOSSES DISTRIBUTION ANALYSIS")
print(f"{'='*80}")

# Sort trades by entry time to get proper sequence
df_sorted = df.sort_values('entry_time').reset_index(drop=True)

# Create win/loss indicator (1 for win, -1 for loss)
df_sorted['result_type'] = df_sorted['pl_points'].apply(lambda x: 1 if x > 0 else -1)

# Function to calculate consecutive streaks
def calculate_streaks(results):
    streaks = []
    current_streak = 1
    current_type = results[0]
    
    for i in range(1, len(results)):
        if results[i] == current_type:
            current_streak += 1
        else:
            streaks.append((current_type, current_streak))
            current_type = results[i]
            current_streak = 1
    
    # Add the last streak
    streaks.append((current_type, current_streak))
    return streaks

# Calculate all streaks
all_streaks = calculate_streaks(df_sorted['result_type'].tolist())

# Separate wins and losses
win_streaks = [length for streak_type, length in all_streaks if streak_type == 1]
loss_streaks = [length for streak_type, length in all_streaks if streak_type == -1]

# Count frequency of each streak length
from collections import Counter
win_streak_counts = Counter(win_streaks)
loss_streak_counts = Counter(loss_streaks)

print(f"CONSECUTIVE WINS DISTRIBUTION:")
print(f"{'Streak Length':<15} {'Frequency':<12} {'Percentage':<12} {'Total Trades':<12}")
print("-" * 60)

total_win_streaks = len(win_streaks)
total_wins_in_streaks = sum(win_streaks)

for streak_length in sorted(win_streak_counts.keys()):
    frequency = win_streak_counts[streak_length]
    percentage = (frequency / total_win_streaks) * 100
    total_trades = streak_length * frequency
    print(f"{streak_length:<15} {frequency:<12} {percentage:<12.1f} {total_trades:<12}")

print(f"\nTotal Win Streaks: {total_win_streaks}")
print(f"Total Winning Trades: {total_wins_in_streaks}")
print(f"Longest Win Streak: {max(win_streaks)} trades")
print(f"Average Win Streak: {np.mean(win_streaks):.1f} trades")

print(f"\n{'-'*60}")
print(f"CONSECUTIVE LOSSES DISTRIBUTION:")
print(f"{'Streak Length':<15} {'Frequency':<12} {'Percentage':<12} {'Total Trades':<12}")
print("-" * 60)

total_loss_streaks = len(loss_streaks)
total_losses_in_streaks = sum(loss_streaks)

for streak_length in sorted(loss_streak_counts.keys()):
    frequency = loss_streak_counts[streak_length]
    percentage = (frequency / total_loss_streaks) * 100
    total_trades = streak_length * frequency
    print(f"{streak_length:<15} {frequency:<12} {percentage:<12.1f} {total_trades:<12}")

print(f"\nTotal Loss Streaks: {total_loss_streaks}")
print(f"Total Losing Trades: {total_losses_in_streaks}")
print(f"Longest Loss Streak: {max(loss_streaks)} trades")
print(f"Average Loss Streak: {np.mean(loss_streaks):.1f} trades")

# Additional streak statistics
print(f"\n{'='*60}")
print("STREAK ANALYSIS SUMMARY")
print(f"{'='*60}")
print(f"Win Rate: {(total_wins_in_streaks / len(df_sorted)) * 100:.2f}%")
print(f"Total Streaks: {len(all_streaks)}")
print(f"Win Streaks: {total_win_streaks} ({(total_win_streaks/len(all_streaks))*100:.1f}%)")
print(f"Loss Streaks: {total_loss_streaks} ({(total_loss_streaks/len(all_streaks))*100:.1f}%)")

# Probability analysis
print(f"\nSTREAK PROBABILITY INSIGHTS:")
print(f"Probability of 2+ consecutive wins: {sum(f for l, f in win_streak_counts.items() if l >= 2) / total_win_streaks * 100:.1f}%")
print(f"Probability of 3+ consecutive wins: {sum(f for l, f in win_streak_counts.items() if l >= 3) / total_win_streaks * 100:.1f}%")
print(f"Probability of 5+ consecutive wins: {sum(f for l, f in win_streak_counts.items() if l >= 5) / total_win_streaks * 100:.1f}%")
print(f"Probability of 5+ consecutive losses: {sum(f for l, f in loss_streak_counts.items() if l >= 5) / total_loss_streaks * 100:.1f}%")
print(f"Probability of 10+ consecutive losses: {sum(f for l, f in loss_streak_counts.items() if l >= 10) / total_loss_streaks * 100:.1f}%")
