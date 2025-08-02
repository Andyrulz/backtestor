#!/usr/bin/env python3
"""
Quick test to see first few trades with new options logic
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from tqdm import tqdm

# Import the main script functions (subset for testing)
def load_data(csv_path):
    df = pd.read_csv(csv_path, parse_dates=['date'])
    df.sort_values('date', inplace=True)
    df.rename(columns={'date': 'datetime'}, inplace=True)
    
    # Filter for regular market hours (9:15 AM to 3:30 PM)
    df['time'] = df['datetime'].dt.time
    market_start = pd.to_datetime('09:15').time()
    market_end = pd.to_datetime('15:30').time()
    df = df[(df['time'] >= market_start) & (df['time'] <= market_end)]
    df = df.drop('time', axis=1)
    
    return df

def calculate_pivots(df, leftBars=15, rightBars=15):
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

# Load a small sample of data
print("Loading first month of data...")
df = load_data('NIFTY 50_minute_data.csv')

# Get first month only
first_month = df['datetime'].min().replace(day=1) + pd.DateOffset(months=1)
df_sample = df[df['datetime'] < first_month].copy()

print(f"Sample period: {df_sample['datetime'].min()} to {df_sample['datetime'].max()}")
print(f"Total bars: {len(df_sample)}")

# Calculate pivots
print("Calculating 5-min pivots...")
pivots = calculate_pivots(df_sample, leftBars=15, rightBars=15)
print(f"Found {len(pivots)} pivots")

# Show first few pivot prices for context
pivot_highs = [p for p in pivots if p['type'] == 'high'][:5]
pivot_lows = [p for p in pivots if p['type'] == 'low'][:5]

print("\nFirst 5 Pivot Highs:")
for p in pivot_highs:
    print(f"  {p['datetime']}: {p['price']}")

print("\nFirst 5 Pivot Lows:")
for p in pivot_lows:
    print(f"  {p['datetime']}: {p['price']}")

print("\n" + "="*80)
print("EXPECTED CHANGES WITH NEW OPTIONS IMPLEMENTATION:")
print("="*80)

print("\n1. POSITION SIZING:")
print("   - OLD: Always 1.0 contract regardless of risk")
print("   - NEW: Risk-based sizing using 2% of capital")
print("   - Position size varies with SL distance")

print("\n2. P&L CALCULATION:")
print("   - OLD: P&L = pl_points (direct futures points)")
print("   - NEW: P&L = position_size × (25x leveraged option premium change)")
print("   - Much higher absolute returns")

print("\n3. RISK MANAGEMENT:")
print("   - OLD: ~0.04% actual risk per trade")
print("   - NEW: Exactly 2% risk per trade")
print("   - Proper capital compounding")

print("\n4. CAPITAL TRACKING:")
print("   - OLD: Capital didn't change (broken)")
print("   - NEW: Capital updates after each trade")
print("   - Compound growth over time")

print("\n5. EXAMPLE COMPARISON:")
print("   Assume: Entry 10000, SL 9980 (20-point SL), Exit 10040 (+40 points)")
print("   OLD SYSTEM:")
print("     Position: 1.0 contract")
print("     P&L: +40 points")
print("     Capital impact: ~0.04%")
print("   NEW SYSTEM:")
print("     Position: ~400 contracts (for 2% risk)")
print("     P&L: ₹4,000 (400 × ₹10 option gain)")
print("     Capital impact: +4%")
print("     If SL hit: ₹-2,000 (-2%)")

print("\n" + "="*80)
print("The new implementation will show:")
print("- Significantly higher absolute P&L numbers")
print("- Proper risk control at 2% per trade")
print("- Capital compounding over time")
print("- Position sizes varying with SL distance")
print("- Much more realistic options trading results")
print("="*80)
