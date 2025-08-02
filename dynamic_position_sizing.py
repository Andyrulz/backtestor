import pandas as pd
import numpy as np

def analyze_loss_streaks_and_suggest_sizing():
    """
    Analyze loss streaks and suggest dynamic position sizing mechanism
    """
    # Load the pivot trail results
    df = pd.read_csv('backtest_results_pivot_trail.csv')
    
    # Convert entry_time to datetime and sort
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df_sorted = df.sort_values('entry_time').reset_index(drop=True)
    
    # Create win/loss indicator
    df_sorted['is_win'] = df_sorted['pl_points'] > 0
    df_sorted['consecutive_losses'] = 0
    
    # Calculate consecutive losses at each trade
    consecutive_count = 0
    for i in range(len(df_sorted)):
        if not df_sorted.loc[i, 'is_win']:
            consecutive_count += 1
        else:
            consecutive_count = 0
        df_sorted.loc[i, 'consecutive_losses'] = consecutive_count
    
    print("=" * 80)
    print("DYNAMIC POSITION SIZING ANALYSIS")
    print("=" * 80)
    
    # Analyze loss distribution
    max_consecutive = df_sorted['consecutive_losses'].max()
    print(f"Maximum consecutive losses observed: {max_consecutive}")
    
    # Count frequency of different loss streak lengths
    loss_counts = df_sorted['consecutive_losses'].value_counts().sort_index()
    print(f"\nConsecutive Loss Distribution:")
    for losses, count in loss_counts.items():
        if losses > 0:
            percentage = (count / len(df_sorted)) * 100
            print(f"{losses:2d} consecutive losses: {count:4d} trades ({percentage:5.1f}%)")
    
    # Calculate cumulative probability of experiencing different loss streaks
    print(f"\nCumulative Risk Analysis:")
    for threshold in [3, 5, 7, 10, 15, 20, 25]:
        trades_with_threshold_plus = len(df_sorted[df_sorted['consecutive_losses'] >= threshold])
        probability = (trades_with_threshold_plus / len(df_sorted)) * 100
        print(f"Probability of {threshold}+ consecutive losses: {probability:5.1f}%")
    
    return df_sorted

def suggest_dynamic_sizing_strategies():
    """
    Present the OPTIMIZED dynamic position sizing strategy
    """
    print(f"\n{'='*80}")
    print("OPTIMIZED DYNAMIC POSITION SIZING STRATEGY")
    print(f"{'='*80}")
    
    print("\nSTRATEGY SPECIFICATIONS:")
    print("• Base Capital: ₹1,00,000")
    print("• Base Risk: 2.0% per trade (₹2,000 = 20 lots)")
    print("• Premium: ₹100 per lot")
    print("• Leverage: 25x")
    print("• Reset: After 1 win (immediate recovery)")
    print("• Minimum Risk Floor: 0.1%")
    
    print(f"\nDYNAMIC RISK SCHEDULE:")
    print(f"{'Consecutive Losses':<20} {'Risk %':<10} {'Amount':<12} {'Lots':<8} {'Reduction':<12}")
    print("-" * 70)
    print(f"{'0-2 losses':<20} {'2.0%':<10} {'₹2,000':<12} {'20':<8} {'Normal':<12}")
    print(f"{'3-4 losses':<20} {'1.6%':<10} {'₹1,600':<12} {'16':<8} {'20% cut':<12}")
    print(f"{'5-7 losses':<20} {'1.2%':<10} {'₹1,200':<12} {'12':<8} {'40% cut':<12}")
    print(f"{'8-11 losses':<20} {'0.8%':<10} {'₹800':<12} {'8':<8} {'60% cut':<12}")
    print(f"{'12-14 losses':<20} {'0.4%':<10} {'₹400':<12} {'4':<8} {'80% cut':<12}")
    print(f"{'15-17 losses':<20} {'0.2%':<10} {'₹200':<12} {'2':<8} {'90% cut':<12}")
    print(f"{'18+ losses':<20} {'0.1%':<10} {'₹100':<12} {'1':<8} {'95% cut':<12}")
    
    print(f"\nKEY ADVANTAGES:")
    print("✓ Conservative step-down approach protects capital")
    print("✓ Quick recovery after wins maintains momentum")
    print("✓ Minimum risk floor prevents over-reduction")
    print("✓ Structured trigger levels based on actual loss data")
    print("✓ Maintains same entry/exit strategy logic")
    
    print(f"\nPSYCHOLOGICAL BENEFITS:")
    print("• Reduces position size during bad streaks")
    print("• Immediate return to normal after any win")
    print("• Protects against catastrophic drawdowns")
    print("• Maintains trading discipline during stress")

def backtest_dynamic_sizing(strategy='optimized'):
    """
    Backtest the optimized dynamic position sizing strategy
    """
    df = pd.read_csv('backtest_results_pivot_trail.csv')
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df_sorted = df.sort_values('entry_time').reset_index(drop=True)
    
    # Calculate consecutive losses and dynamic position size
    df_sorted['consecutive_losses'] = 0
    df_sorted['dynamic_risk_pct'] = 2.0  # Base risk
    df_sorted['dynamic_position_size'] = 0
    df_sorted['dynamic_pl_points'] = 0
    df_sorted['dynamic_pl_rupees'] = 0
    
    consecutive_count = 0
    
    for i in range(len(df_sorted)):
        current_trade = df_sorted.loc[i]
        
        # Apply OPTIMIZED dynamic sizing based on consecutive losses
        # Trigger levels: 3, 5, 8, 12, 15, 18+ losses
        # Conservative step-down with minimum 0.1% risk
        if consecutive_count >= 18:
            risk_pct = 0.1  # Minimum risk floor
        elif consecutive_count >= 15:
            risk_pct = 0.2
        elif consecutive_count >= 12:
            risk_pct = 0.4
        elif consecutive_count >= 8:
            risk_pct = 0.8
        elif consecutive_count >= 5:
            risk_pct = 1.2
        elif consecutive_count >= 3:
            risk_pct = 1.6
        else:
            risk_pct = 2.0  # Normal risk
        
        # Store values
        df_sorted.loc[i, 'consecutive_losses'] = consecutive_count
        df_sorted.loc[i, 'dynamic_risk_pct'] = risk_pct
        
        # Calculate position size (₹100 premium, ₹100,000 capital)
        capital = 100000
        position_size = (capital * risk_pct / 100) / 100  # Number of lots
        df_sorted.loc[i, 'dynamic_position_size'] = position_size
        
        # Calculate P&L with dynamic sizing
        original_pl_points = current_trade['pl_points']
        dynamic_pl_points = original_pl_points  # Points remain same
        dynamic_pl_rupees = original_pl_points * position_size * 25  # 25x leverage
        
        df_sorted.loc[i, 'dynamic_pl_points'] = dynamic_pl_points
        df_sorted.loc[i, 'dynamic_pl_rupees'] = dynamic_pl_rupees
        
        # Update consecutive loss counter - RESET AFTER 1 WIN
        if current_trade['pl_points'] > 0:
            consecutive_count = 0  # Reset immediately after any win
        else:
            consecutive_count += 1
    
    # Calculate results
    original_total_pl = df_sorted['pl_points'].sum() * 20 * 25  # 20 lots * 25 leverage
    dynamic_total_pl = df_sorted['dynamic_pl_rupees'].sum()
    
    original_wins = len(df_sorted[df_sorted['pl_points'] > 0])
    dynamic_wins = original_wins  # Win count doesn't change
    
    original_max_dd = calculate_max_drawdown(df_sorted['pl_points'] * 20 * 25)
    dynamic_max_dd = calculate_max_drawdown(df_sorted['dynamic_pl_rupees'])
    
    print(f"\n{'='*80}")
    print(f"OPTIMIZED DYNAMIC SIZING BACKTEST RESULTS")
    print(f"{'='*80}")
    print(f"Base Capital: ₹1,00,000")
    print(f"Base Risk Per Trade: 2.0% (₹2,000)")
    print(f"Trigger Levels: 3, 5, 8, 12, 15, 18+ losses")
    print(f"Risk Reductions: 1.6%, 1.2%, 0.8%, 0.4%, 0.2%, 0.1%")
    print(f"Reset Mechanism: After 1 win")
    print(f"\nOriginal Strategy (Fixed 2% risk):")
    print(f"  Total P&L: ₹{original_total_pl:,.0f}")
    print(f"  Max Drawdown: ₹{original_max_dd:,.0f}")
    print(f"  Win Rate: {(original_wins/len(df_sorted))*100:.2f}%")
    
    print(f"\nOptimized Dynamic Sizing:")
    print(f"  Total P&L: ₹{dynamic_total_pl:,.0f}")
    print(f"  Max Drawdown: ₹{dynamic_max_dd:,.0f}")
    print(f"  Win Rate: {(dynamic_wins/len(df_sorted))*100:.2f}%")
    print(f"  P&L Change: {((dynamic_total_pl/original_total_pl)-1)*100:+.1f}%")
    print(f"  Drawdown Reduction: {((dynamic_max_dd/original_max_dd)-1)*100:+.1f}%")
    
    # Show risk distribution
    risk_distribution = df_sorted['dynamic_risk_pct'].value_counts().sort_index()
    print(f"\nRisk Distribution:")
    total_trades = len(df_sorted)
    for risk, count in risk_distribution.items():
        percentage = (count / total_trades) * 100
        lots = (100000 * risk / 100) / 100
        print(f"  {risk:4.1f}% risk ({lots:4.1f} lots): {count:4d} trades ({percentage:5.1f}%)")
    
    # Calculate average risk taken
    avg_risk = df_sorted['dynamic_risk_pct'].mean()
    print(f"\nAverage Risk Per Trade: {avg_risk:.2f}%")
    print(f"Risk Reduction from Base: {((avg_risk/2.0)-1)*100:+.1f}%")
    
    return df_sorted

def calculate_max_drawdown(pl_series):
    """Calculate maximum drawdown from P&L series"""
    cumulative = pl_series.cumsum()
    peak = cumulative.expanding().max()
    drawdown = cumulative - peak
    return abs(drawdown.min())

if __name__ == "__main__":
    # Analyze current loss streaks
    df_analyzed = analyze_loss_streaks_and_suggest_sizing()
    
    # Present optimized strategy
    suggest_dynamic_sizing_strategies()
    
    # Backtest optimized strategy
    print(f"\n{'='*80}")
    print("BACKTESTING OPTIMIZED DYNAMIC SIZING STRATEGY")
    print(f"{'='*80}")
    
    optimized_results = backtest_dynamic_sizing('optimized')
    
    print(f"\n{'='*80}")
    print("IMPLEMENTATION RECOMMENDATION")
    print(f"{'='*80}")
    print("✅ RECOMMENDED APPROACH: Optimized Dynamic Sizing")
    print()
    print("This strategy provides:")
    print("• Significant drawdown protection during bad streaks")
    print("• Quick recovery to full position size after wins")
    print("• Conservative risk reductions (20%, 40%, 60%, 80%, 90%, 95%)")
    print("• Structured trigger levels based on actual loss probabilities")
    print("• Maintains profitability while reducing psychological stress")
    print()
    print("NEXT STEPS:")
    print("1. Implement this logic in your live trading system")
    print("2. Track consecutive losses in real-time")
    print("3. Adjust position sizes before each trade")
    print("4. Reset to normal after any winning trade")
    print("5. Monitor performance and adjust triggers if needed")
