import pandas as pd
import numpy as np

print("="*80)
print("CLARIFICATION: CURRENT vs PROPOSED POSITION SIZING")
print("="*80)

print("\n🔍 CURRENT SYSTEM (What you already have):")
print("-" * 50)

sample_capital = 1000000  # ₹10 lakh for easier examples
fixed_risk = 0.02  # 2%

print(f"Capital: ₹{sample_capital:,}")
print(f"Fixed Risk: {fixed_risk*100}%")
print(f"Risk Amount: ₹{sample_capital * fixed_risk:,}")
print()

print("Position sizing examples:")
print(f"{'SL Distance':<12} {'Position Size':<15} {'Risk Amount':<15} {'Quality'}")
print("-" * 65)

examples = [
    (5, "High Quality"),
    (8, "Good Quality"), 
    (10, "Average"),
    (15, "Poor Quality"),
    (20, "Very Poor"),
]

for sl, quality in examples:
    position = (sample_capital * fixed_risk) / sl
    risk_amount = sample_capital * fixed_risk
    print(f"{sl:2d} points     ₹{position:>10,.0f}      ₹{risk_amount:>10,.0f}      {quality}")

print(f"\n📝 KEY OBSERVATION:")
print("• Position size DOES automatically adjust for SL distance")
print("• BUT risk amount stays CONSTANT at ₹20,000 regardless of setup quality")
print("• We discovered that SL distance correlates with SETUP QUALITY!")

print(f"\n🚀 PROPOSED SMART SYSTEM (What we want to add):")
print("-" * 50)

print("RISK PERCENTAGE adjustment based on setup quality:")
print(f"{'SL Distance':<12} {'Risk %':<8} {'Risk Amount':<15} {'Position Size':<15} {'Reasoning'}")
print("-" * 85)

smart_examples = [
    (5, 0.03, "High Quality - Increase risk"),
    (8, 0.025, "Good Quality - Slight increase"), 
    (10, 0.02, "Average - Keep same"),
    (15, 0.015, "Poor Quality - Reduce risk"),
    (20, 0.01, "Very Poor - Significantly reduce"),
]

for sl, risk_pct, reasoning in smart_examples:
    risk_amount = sample_capital * risk_pct
    position = risk_amount / sl
    print(f"{sl:2d} points     {risk_pct*100:>4.1f}%    ₹{risk_amount:>10,.0f}      ₹{position:>10,.0f}      {reasoning}")

print(f"\n🎯 THE DIFFERENCE:")
print("=" * 50)

print("CURRENT: Position Size = (Capital × 2%) ÷ SL Distance")
print("PROPOSED: Position Size = (Capital × SMART_RISK%) ÷ SL Distance")
print()
print("Where SMART_RISK% varies from 1% to 3% based on setup quality!")

print(f"\n💡 WHY THIS WORKS:")
print("-" * 30)
print("1. Tight SL setups (≤7pts) = High-quality breakouts")
print("   → Clear, decisive moves → Deserve MORE capital")
print("   → Increase risk from 2% to 3% = 50% more profit potential")
print()
print("2. Wide SL setups (>15pts) = Poor-quality/desperate entries") 
print("   → Sloppy, uncertain moves → Deserve LESS capital")
print("   → Reduce risk from 2% to 1% = Limit damage from bad setups")

print(f"\n📊 REAL EXAMPLE COMPARISON:")
print("-" * 40)

print("Scenario: ₹10,00,000 capital, 5-point tight SL breakout")
print()
print("CURRENT SYSTEM:")
current_risk = 1000000 * 0.02
current_position = current_risk / 5
print(f"  Risk: 2% = ₹{current_risk:,.0f}")
print(f"  Position: ₹{current_position:,.0f}")
print(f"  If trade wins +15pts: Profit = ₹{current_position * 15:,.0f}")

print()
print("SMART SYSTEM (recognizing high-quality setup):")
smart_risk = 1000000 * 0.03  # 3% for tight SL
smart_position = smart_risk / 5
print(f"  Risk: 3% = ₹{smart_risk:,.0f}")
print(f"  Position: ₹{smart_position:,.0f}")
print(f"  If trade wins +15pts: Profit = ₹{smart_position * 15:,.0f}")

profit_difference = (smart_position - current_position) * 15
print(f"  EXTRA PROFIT: ₹{profit_difference:,.0f} (+50% more!)")

print(f"\n🔑 SUMMARY:")
print("=" * 30)
print("• We are NOT changing the SL-based position sizing logic")
print("• We are adding SETUP QUALITY recognition")
print("• Tight SL = High quality = Increase risk percentage")
print("• Wide SL = Poor quality = Decrease risk percentage")
print("• Result: More capital on good setups, less on bad ones")
print("• Potential: +29.7% improvement in total P&L!")

print(f"\n🛠️ IMPLEMENTATION:")
print("-" * 25)
print("def get_smart_risk_percentage(sl_distance, entry_hour, direction):")
print("    base_risk = 0.02  # 2%")
print("    ")
print("    # Setup quality multiplier")
print("    if sl_distance <= 7:")
print("        quality_multiplier = 1.5  # High quality")
print("    elif sl_distance > 15:")
print("        quality_multiplier = 0.75  # Poor quality")
print("    else:")
print("        quality_multiplier = 1.0  # Average")
print("    ")
print("    # Time and direction adjustments...")
print("    # (Additional factors)")
print("    ")
print("    return base_risk * quality_multiplier")
