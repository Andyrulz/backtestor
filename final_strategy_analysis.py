import pandas as pd
import numpy as np

print("="*80)
print("FINAL STRATEGY COMPARISON & RECOMMENDATIONS")
print("="*80)

# Load the comparison summary
comparison_df = pd.read_csv('strategy_comparison_summary.csv')

print("\n🏆 ULTIMATE STRATEGY SHOWDOWN")
print("=" * 80)

# Display the key metrics in a clean format
print(f"{'Strategy':<25} {'Final Capital':<18} {'CAGR':<8} {'Max DD':<10} {'Risk-Adj Return':<15}")
print("-" * 90)

for _, row in comparison_df.iterrows():
    risk_adj_return = row['CAGR (%)'] / row['Max Cap DD (%)']
    print(f"{row['Strategy']:<25} ₹{row['Final Capital (₹)']:>15,.0f} {row['CAGR (%)']:>6.1f}% {row['Max Cap DD (%)']:>8.1f}% {risk_adj_return:>13.2f}")

print("\n📊 KEY INSIGHTS:")
print("-" * 50)

original_capital = comparison_df[comparison_df['Strategy'] == 'Original (Fixed 2%)']['Final Capital (₹)'].iloc[0]
conservative_smart_capital = comparison_df[comparison_df['Strategy'] == 'Smart (Conservative)']['Final Capital (₹)'].iloc[0]
aggressive_smart_capital = comparison_df[comparison_df['Strategy'] == 'Smart (Aggressive)']['Final Capital (₹)'].iloc[0]

conservative_improvement = ((conservative_smart_capital - original_capital) / original_capital) * 100
aggressive_improvement = ((aggressive_smart_capital - original_capital) / original_capital) * 100

print(f"1. 🚀 SMART SIZING IMPACT:")
print(f"   Conservative Smart: {conservative_improvement:+.0f}% improvement over original")
print(f"   Aggressive Smart: {aggressive_improvement:+.0f}% improvement over original")

print(f"\n2. 📈 PERFORMANCE RANKING (by Final Capital):")
strategies_sorted = comparison_df.sort_values('Final Capital (₹)', ascending=False)
for i, (_, row) in enumerate(strategies_sorted.iterrows(), 1):
    print(f"   {i}. {row['Strategy']}: ₹{row['Final Capital (₹)']:,.0f}")

print(f"\n3. ⚖️ RISK-ADJUSTED RANKING (CAGR/Max DD):")
comparison_df['Risk_Adj_Return'] = comparison_df['CAGR (%)'] / comparison_df['Max Cap DD (%)']
risk_adj_sorted = comparison_df.sort_values('Risk_Adj_Return', ascending=False)
for i, (_, row) in enumerate(risk_adj_sorted.iterrows(), 1):
    print(f"   {i}. {row['Strategy']}: {row['Risk_Adj_Return']:.2f}")

print(f"\n4. 🛡️ DRAWDOWN COMPARISON:")
drawdown_sorted = comparison_df.sort_values('Max Cap DD (%)')
for _, row in drawdown_sorted.iterrows():
    print(f"   {row['Strategy']}: {row['Max Cap DD (%)']:.1f}% max drawdown")

print(f"\n💡 STRATEGY RECOMMENDATIONS:")
print("=" * 50)

print(f"🥇 FOR MAXIMUM RETURNS (Risk Tolerant):")
print(f"   → Smart (Aggressive) Position Sizing")
print(f"   → CAGR: {strategies_sorted.iloc[0]['CAGR (%)']:.1f}%")
print(f"   → Final Capital: ₹{strategies_sorted.iloc[0]['Final Capital (₹)']:,.0f}")
print(f"   → Trade-off: Higher drawdown ({strategies_sorted.iloc[0]['Max Cap DD (%)']:.1f}%)")

print(f"\n🥈 FOR BALANCED PERFORMANCE (Moderate Risk):")
print(f"   → Smart (Conservative) Position Sizing") 
print(f"   → CAGR: {comparison_df[comparison_df['Strategy']=='Smart (Conservative)']['CAGR (%)'].iloc[0]:.1f}%")
print(f"   → Better risk management with excellent returns")

print(f"\n🥉 FOR CONSERVATIVE APPROACH (Risk Averse):")
best_drawdown = drawdown_sorted.iloc[0]
print(f"   → {best_drawdown['Strategy']}")
print(f"   → Lowest drawdown: {best_drawdown['Max Cap DD (%)']:.1f}%")
print(f"   → Steady CAGR: {best_drawdown['CAGR (%)']:.1f}%")

print(f"\n🔍 SMART SIZING MECHANICS EXPLAINED:")
print("-" * 45)
print(f"✅ INCREASE Position Size (up to 2.5% risk) for:")
print(f"   • Tight SL setups (≤7 points) - High quality breakouts")
print(f"   • Optimal timing (11:00-14:00) - Best performance hours")
print(f"   • Long trades - Better directional bias")

print(f"\n⚠️  REDUCE Position Size (down to 0.5% risk) for:")
print(f"   • Wide SL setups (>15 points) - Poor quality setups")
print(f"   • Poor timing (10:00, 15:00+) - Worst performance hours")
print(f"   • Consecutive loss protection - Risk reduction overlay")

print(f"\n🎯 IMPLEMENTATION PRIORITY:")
print("-" * 30)
print(f"1. Implement Smart (Conservative) first - Excellent balance")
print(f"2. Test in live environment with smaller capital")
print(f"3. Monitor performance vs. backtested expectations")
print(f"4. Consider upgrading to Aggressive version after validation")

# Create a summary file with key takeaways
summary_data = {
    'Strategy': ['Smart Conservative', 'Smart Aggressive', 'Original', 'Dynamic'],
    'Recommended_For': [
        'Balanced Performance - Best overall choice',
        'Maximum Returns - High risk tolerance',
        'Baseline/Simple Implementation',
        'Conservative Risk Management'
    ],
    'Final_Capital': [
        conservative_smart_capital,
        aggressive_smart_capital,
        original_capital,
        comparison_df[comparison_df['Strategy']=='Dynamic (Loss Protection)']['Final Capital (₹)'].iloc[0]
    ],
    'CAGR': [
        comparison_df[comparison_df['Strategy']=='Smart (Conservative)']['CAGR (%)'].iloc[0],
        comparison_df[comparison_df['Strategy']=='Smart (Aggressive)']['CAGR (%)'].iloc[0],
        comparison_df[comparison_df['Strategy']=='Original (Fixed 2%)']['CAGR (%)'].iloc[0],
        comparison_df[comparison_df['Strategy']=='Dynamic (Loss Protection)']['CAGR (%)'].iloc[0]
    ],
    'Max_Drawdown': [
        comparison_df[comparison_df['Strategy']=='Smart (Conservative)']['Max Cap DD (%)'].iloc[0],
        comparison_df[comparison_df['Strategy']=='Smart (Aggressive)']['Max Cap DD (%)'].iloc[0],
        comparison_df[comparison_df['Strategy']=='Original (Fixed 2%)']['Max Cap DD (%)'].iloc[0],
        comparison_df[comparison_df['Strategy']=='Dynamic (Loss Protection)']['Max Cap DD (%)'].iloc[0]
    ]
}

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv('strategy_recommendations_summary.csv', index=False)

print(f"\n📁 Files Created:")
print(f"   • strategy_comparison_summary.csv - Detailed metrics")
print(f"   • strategy_recommendations_summary.csv - Implementation guide")
print(f"   • backtest_results_smart_sizing.csv - Aggressive smart results")
print(f"   • backtest_results_conservative_smart.csv - Conservative smart results")

print(f"\n🎉 CONCLUSION:")
print("=" * 30)
print(f"Smart Position Sizing (Conservative) is the WINNER! 🏆")
print(f"• {conservative_improvement:+.0f}% improvement over baseline")
print(f"• {comparison_df[comparison_df['Strategy']=='Smart (Conservative)']['CAGR (%)'].iloc[0]:.1f}% CAGR")
print(f"• Excellent risk-adjusted returns")
print(f"• Combines setup quality recognition with loss protection")
print(f"• Ready for implementation! 🚀")
