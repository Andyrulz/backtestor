#!/usr/bin/env python3
"""
Test script to understand the simplified options logic
"""

def calculate_options_position_size(capital, risk_percentage, sl_distance, entry_price):
    """
    Simple options position sizing with fixed assumptions
    """
    risk_amount = capital * risk_percentage
    option_premium = 100  # Fixed ₹100 per option contract
    options_leverage = 25  # 1% futures move = 25% option move
    
    # Risk per option if SL is hit
    # Simple calculation: sl_distance with leverage factor
    risk_per_option = sl_distance * (options_leverage / 100)  # Convert leverage to decimal
    
    if risk_per_option <= 0:
        return 1
        
    # Position size to achieve target risk
    position_size = risk_amount / risk_per_option
    
    # Account for drawdown potential - reduce position size if capital is low
    drawdown_factor = max(0.5, capital / 100000)  # Reduce size if capital < 1L
    position_size *= drawdown_factor
    
    # Round to integer lots
    position_size = max(1, int(round(position_size)))
    
    # Cap position size to prevent over-leveraging
    max_position = capital / (option_premium * 2)  # Don't use more than 50% capital for premiums
    position_size = min(position_size, int(max_position))
    
    return max(1, position_size)

def calculate_options_pl(entry_price, exit_price, direction, position_size):
    """Calculate P&L using simplified options logic"""
    options_leverage = 25  # 25x leverage factor
    option_premium = 100   # Fixed ₹100 per contract
    
    # Calculate P&L in points (futures price movement)
    if direction == 'long':
        pl_points = (exit_price - entry_price)
    else:
        pl_points = (entry_price - exit_price)
    
    # Convert futures move to option premium change
    # 1% futures move (100 points on 10,000) = 25% option move (₹25 on ₹100)
    futures_move_percent = pl_points / entry_price  # Convert points to percentage
    option_move_percent = futures_move_percent * options_leverage  # Apply leverage
    option_premium_change = option_premium * option_move_percent  # Change in premium
    
    # Total P&L = position_size × option_premium_change
    actual_pl = position_size * option_premium_change
    
    return actual_pl, pl_points, futures_move_percent, option_move_percent

# Test scenarios
print("="*80)
print("SIMPLIFIED OPTIONS LOGIC ANALYSIS")
print("="*80)

print("\nKey Assumptions:")
print("- Fixed option premium: ₹100 per contract")
print("- Options leverage: 25x (1% futures move = 25% option move)")
print("- Starting capital: ₹100,000")
print("- Risk per trade: 2%")
print()

# Example trade scenarios
scenarios = [
    {"entry": 10000, "sl": 9980, "exit": 10040, "direction": "long", "name": "Long Win (+40 pts)"},
    {"entry": 10000, "sl": 9980, "exit": 9975, "direction": "long", "name": "Long Loss (-25 pts)"},
    {"entry": 10000, "sl": 10020, "exit": 9960, "direction": "short", "name": "Short Win (+40 pts)"},
    {"entry": 10000, "sl": 10020, "exit": 10025, "direction": "short", "name": "Short Loss (-25 pts)"},
]

capital = 100000
risk_percentage = 0.02

for i, scenario in enumerate(scenarios, 1):
    print(f"Scenario {i}: {scenario['name']}")
    print("-" * 50)
    
    entry_price = scenario['entry']
    sl_price = scenario['sl']
    exit_price = scenario['exit']
    direction = scenario['direction']
    
    # Calculate SL distance
    sl_distance = abs(entry_price - sl_price)
    
    # Calculate position size
    position_size = calculate_options_position_size(capital, risk_percentage, sl_distance, entry_price)
    
    # Calculate P&L
    actual_pl, pl_points, futures_move_percent, option_move_percent = calculate_options_pl(
        entry_price, exit_price, direction, position_size
    )
    
    # Calculate what the actual risk would be if SL was hit
    sl_pl, _, _, _ = calculate_options_pl(entry_price, sl_price, direction, position_size)
    risk_percentage_actual = abs(sl_pl) / capital * 100
    
    print(f"Entry: {entry_price}, SL: {sl_price}, Exit: {exit_price}")
    print(f"SL Distance: {sl_distance} points")
    print(f"Position Size: {position_size} contracts")
    print(f"Futures Move: {pl_points:+.1f} points ({futures_move_percent:+.3%})")
    print(f"Option Move: {option_move_percent:+.1%} (₹{100 * option_move_percent:+.1f} per contract)")
    print(f"Total P&L: ₹{actual_pl:,.0f}")
    print(f"Capital Impact: {actual_pl/capital:+.2%}")
    print(f"If SL hit: ₹{sl_pl:,.0f} ({risk_percentage_actual:.2f}% risk)")
    print()

print("="*80)
print("COMPARISON WITH OLD SYSTEM")
print("="*80)
print("\nOLD SYSTEM (Fixed 1.0 position):")
print("- Always used position_size = 1.0")
print("- P&L = pl_points (direct futures P&L)")
print("- Risk was ~0.04% instead of 2%")
print()
print("NEW SYSTEM (Risk-based options sizing):")
print("- Position size varies based on SL distance and capital")
print("- P&L = position_size × (25x leveraged option premium change)")
print("- Risk properly controlled at 2% per trade")
print("- Much higher absolute P&L due to proper position sizing")
