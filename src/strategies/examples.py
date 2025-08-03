"""Example trading strategies for demonstration and testing."""

import pandas as pd
import numpy as np
from typing import Dict, Any

from .base import (
    BaseStrategy, 
    StrategyConfig, 
    StrategySignalData, 
    StrategySignal,
    TechnicalIndicators
)
from kite.client import KiteClient


class MovingAverageCrossover(BaseStrategy):
    """Moving Average Crossover Strategy.
    
    Generates BUY signal when fast MA crosses above slow MA.
    Generates SELL signal when fast MA crosses below slow MA.
    """
    
    def __init__(self, config: StrategyConfig, kite_client: KiteClient, 
                 fast_period: int = 10, slow_period: int = 20):
        """Initialize Moving Average Crossover strategy.
        
        Args:
            config: Strategy configuration
            kite_client: Kite API client
            fast_period: Fast moving average period
            slow_period: Slow moving average period
        """
        super().__init__(config, kite_client)
        self.fast_period = fast_period
        self.slow_period = slow_period
        
    def analyze(self, symbol: str, data: pd.DataFrame) -> StrategySignalData:
        """Analyze data using moving average crossover.
        
        Args:
            symbol: Trading symbol
            data: Historical OHLC data
            
        Returns:
            Strategy signal
        """
        if len(data) < self.slow_period:
            return StrategySignalData(
                symbol=symbol,
                signal=StrategySignal.HOLD,
                confidence=0.0,
                metadata={'error': 'Insufficient data'}
            )
        
        # Calculate moving averages
        data['fast_ma'] = TechnicalIndicators.sma(data['close'], self.fast_period)
        data['slow_ma'] = TechnicalIndicators.sma(data['close'], self.slow_period)
        
        # Get latest values
        current_fast = data['fast_ma'].iloc[-1]
        current_slow = data['slow_ma'].iloc[-1]
        prev_fast = data['fast_ma'].iloc[-2]
        prev_slow = data['slow_ma'].iloc[-2]
        current_price = data['close'].iloc[-1]
        
        # Check for crossover
        signal = StrategySignal.HOLD
        confidence = 0.5
        
        # Bullish crossover (fast MA crosses above slow MA)
        if prev_fast <= prev_slow and current_fast > current_slow:
            signal = StrategySignal.BUY
            confidence = 0.8
            
        # Bearish crossover (fast MA crosses below slow MA)
        elif prev_fast >= prev_slow and current_fast < current_slow:
            signal = StrategySignal.SELL
            confidence = 0.8
        
        # Calculate entry, stop loss, and take profit
        entry_price = current_price
        stop_loss = entry_price * (1 - self.config.stop_loss_pct) if signal == StrategySignal.BUY else entry_price * (1 + self.config.stop_loss_pct)
        take_profit = entry_price * (1 + self.config.take_profit_pct) if signal == StrategySignal.BUY else entry_price * (1 - self.config.take_profit_pct)
        
        return StrategySignalData(
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata={
                'fast_ma': current_fast,
                'slow_ma': current_slow,
                'fast_period': self.fast_period,
                'slow_period': self.slow_period
            }
        )
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> int:
        """Calculate position size based on risk management.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            
        Returns:
            Position size
        """
        risk_amount = self.config.capital * self.config.risk_per_trade
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff == 0:
            return 1
        
        position_size = int(risk_amount / price_diff)
        return max(1, min(position_size, 1000))  # Between 1 and 1000 shares


class RSIStrategy(BaseStrategy):
    """RSI-based mean reversion strategy.
    
    Generates BUY signal when RSI is oversold (< 30).
    Generates SELL signal when RSI is overbought (> 70).
    """
    
    def __init__(self, config: StrategyConfig, kite_client: KiteClient,
                 rsi_period: int = 14, oversold: float = 30, overbought: float = 70):
        """Initialize RSI strategy.
        
        Args:
            config: Strategy configuration
            kite_client: Kite API client
            rsi_period: RSI calculation period
            oversold: Oversold threshold
            overbought: Overbought threshold
        """
        super().__init__(config, kite_client)
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> StrategySignalData:
        """Analyze data using RSI.
        
        Args:
            symbol: Trading symbol
            data: Historical OHLC data
            
        Returns:
            Strategy signal
        """
        if len(data) < self.rsi_period + 1:
            return StrategySignalData(
                symbol=symbol,
                signal=StrategySignal.HOLD,
                confidence=0.0,
                metadata={'error': 'Insufficient data'}
            )
        
        # Calculate RSI
        data['rsi'] = TechnicalIndicators.rsi(data['close'], self.rsi_period)
        
        current_rsi = data['rsi'].iloc[-1]
        current_price = data['close'].iloc[-1]
        
        # Generate signals
        signal = StrategySignal.HOLD
        confidence = 0.5
        
        if current_rsi < self.oversold:
            signal = StrategySignal.BUY
            confidence = min(0.9, (self.oversold - current_rsi) / self.oversold + 0.6)
            
        elif current_rsi > self.overbought:
            signal = StrategySignal.SELL
            confidence = min(0.9, (current_rsi - self.overbought) / (100 - self.overbought) + 0.6)
        
        # Calculate levels
        entry_price = current_price
        stop_loss = entry_price * (1 - self.config.stop_loss_pct) if signal == StrategySignal.BUY else entry_price * (1 + self.config.stop_loss_pct)
        take_profit = entry_price * (1 + self.config.take_profit_pct) if signal == StrategySignal.BUY else entry_price * (1 - self.config.take_profit_pct)
        
        return StrategySignalData(
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata={
                'rsi': current_rsi,
                'rsi_period': self.rsi_period,
                'oversold_threshold': self.oversold,
                'overbought_threshold': self.overbought
            }
        )
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> int:
        """Calculate position size based on risk management."""
        risk_amount = self.config.capital * self.config.risk_per_trade
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff == 0:
            return 1
        
        position_size = int(risk_amount / price_diff)
        return max(1, min(position_size, 1000))


class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands mean reversion strategy.
    
    Generates BUY signal when price touches lower band.
    Generates SELL signal when price touches upper band.
    """
    
    def __init__(self, config: StrategyConfig, kite_client: KiteClient,
                 bb_period: int = 20, bb_std: float = 2.0):
        """Initialize Bollinger Bands strategy.
        
        Args:
            config: Strategy configuration
            kite_client: Kite API client
            bb_period: Bollinger Bands period
            bb_std: Standard deviation multiplier
        """
        super().__init__(config, kite_client)
        self.bb_period = bb_period
        self.bb_std = bb_std
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> StrategySignalData:
        """Analyze data using Bollinger Bands.
        
        Args:
            symbol: Trading symbol
            data: Historical OHLC data
            
        Returns:
            Strategy signal
        """
        if len(data) < self.bb_period:
            return StrategySignalData(
                symbol=symbol,
                signal=StrategySignal.HOLD,
                confidence=0.0,
                metadata={'error': 'Insufficient data'}
            )
        
        # Calculate Bollinger Bands
        bb = TechnicalIndicators.bollinger_bands(data['close'], self.bb_period, self.bb_std)
        data['bb_upper'] = bb['upper']
        data['bb_middle'] = bb['middle']
        data['bb_lower'] = bb['lower']
        
        current_price = data['close'].iloc[-1]
        current_upper = data['bb_upper'].iloc[-1]
        current_lower = data['bb_lower'].iloc[-1]
        current_middle = data['bb_middle'].iloc[-1]
        
        # Generate signals
        signal = StrategySignal.HOLD
        confidence = 0.5
        
        # Price near lower band - potential buy
        if current_price <= current_lower:
            signal = StrategySignal.BUY
            distance_ratio = (current_lower - current_price) / (current_upper - current_lower)
            confidence = min(0.9, 0.7 + distance_ratio)
            
        # Price near upper band - potential sell
        elif current_price >= current_upper:
            signal = StrategySignal.SELL
            distance_ratio = (current_price - current_upper) / (current_upper - current_lower)
            confidence = min(0.9, 0.7 + distance_ratio)
        
        # Calculate levels
        entry_price = current_price
        if signal == StrategySignal.BUY:
            stop_loss = current_lower * 0.98  # Slightly below lower band
            take_profit = current_middle  # Target middle band
        elif signal == StrategySignal.SELL:
            stop_loss = current_upper * 1.02  # Slightly above upper band
            take_profit = current_middle  # Target middle band
        else:
            stop_loss = entry_price * (1 - self.config.stop_loss_pct)
            take_profit = entry_price * (1 + self.config.take_profit_pct)
        
        return StrategySignalData(
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata={
                'bb_upper': current_upper,
                'bb_middle': current_middle,
                'bb_lower': current_lower,
                'bb_period': self.bb_period,
                'bb_std': self.bb_std,
                'price_position': 'lower' if current_price <= current_lower else 'upper' if current_price >= current_upper else 'middle'
            }
        )
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> int:
        """Calculate position size based on risk management."""
        risk_amount = self.config.capital * self.config.risk_per_trade
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff == 0:
            return 1
        
        position_size = int(risk_amount / price_diff)
        return max(1, min(position_size, 1000))


class MACDStrategy(BaseStrategy):
    """MACD momentum strategy.
    
    Generates BUY signal when MACD crosses above signal line.
    Generates SELL signal when MACD crosses below signal line.
    """
    
    def __init__(self, config: StrategyConfig, kite_client: KiteClient,
                 fast: int = 12, slow: int = 26, signal_period: int = 9):
        """Initialize MACD strategy.
        
        Args:
            config: Strategy configuration
            kite_client: Kite API client
            fast: Fast EMA period
            slow: Slow EMA period
            signal_period: Signal line EMA period
        """
        super().__init__(config, kite_client)
        self.fast = fast
        self.slow = slow
        self.signal_period = signal_period
    
    def analyze(self, symbol: str, data: pd.DataFrame) -> StrategySignalData:
        """Analyze data using MACD.
        
        Args:
            symbol: Trading symbol
            data: Historical OHLC data
            
        Returns:
            Strategy signal
        """
        if len(data) < self.slow + self.signal_period:
            return StrategySignalData(
                symbol=symbol,
                signal=StrategySignal.HOLD,
                confidence=0.0,
                metadata={'error': 'Insufficient data'}
            )
        
        # Calculate MACD
        macd_data = TechnicalIndicators.macd(data['close'], self.fast, self.slow, self.signal_period)
        data['macd'] = macd_data['macd']
        data['macd_signal'] = macd_data['signal']
        data['macd_histogram'] = macd_data['histogram']
        
        current_macd = data['macd'].iloc[-1]
        current_signal = data['macd_signal'].iloc[-1]
        prev_macd = data['macd'].iloc[-2]
        prev_signal = data['macd_signal'].iloc[-2]
        current_price = data['close'].iloc[-1]
        
        # Generate signals based on MACD crossover
        signal = StrategySignal.HOLD
        confidence = 0.5
        
        # Bullish crossover (MACD crosses above signal)
        if prev_macd <= prev_signal and current_macd > current_signal:
            signal = StrategySignal.BUY
            confidence = 0.8
            
        # Bearish crossover (MACD crosses below signal)
        elif prev_macd >= prev_signal and current_macd < current_signal:
            signal = StrategySignal.SELL
            confidence = 0.8
        
        # Calculate levels
        entry_price = current_price
        stop_loss = entry_price * (1 - self.config.stop_loss_pct) if signal == StrategySignal.BUY else entry_price * (1 + self.config.stop_loss_pct)
        take_profit = entry_price * (1 + self.config.take_profit_pct) if signal == StrategySignal.BUY else entry_price * (1 - self.config.take_profit_pct)
        
        return StrategySignalData(
            symbol=symbol,
            signal=signal,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata={
                'macd': current_macd,
                'macd_signal': current_signal,
                'macd_histogram': data['macd_histogram'].iloc[-1],
                'fast_period': self.fast,
                'slow_period': self.slow,
                'signal_period': self.signal_period
            }
        )
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> int:
        """Calculate position size based on risk management."""
        risk_amount = self.config.capital * self.config.risk_per_trade
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff == 0:
            return 1
        
        position_size = int(risk_amount / price_diff)
        return max(1, min(position_size, 1000))
