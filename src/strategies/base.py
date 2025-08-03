"""Base strategy class and enums for the trading system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
from kite.models import Candle, Order, Position, OrderRequest
from kite.client import KiteClient


class StrategySignal(Enum):
    """Strategy signals."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    EXIT = "EXIT"


class StrategyStatus(Enum):
    """Strategy execution status."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


@dataclass
class StrategyConfig:
    """Base configuration for strategies."""
    name: str
    symbols: List[str]
    timeframe: str = "5minute"
    capital: float = 100000.0
    max_positions: int = 5
    risk_per_trade: float = 0.02  # 2% risk per trade
    stop_loss_pct: float = 0.05   # 5% stop loss
    take_profit_pct: float = 0.10  # 10% take profit
    enabled: bool = True


@dataclass
class StrategySignalData:
    """Signal data from strategy analysis."""
    symbol: str
    signal: StrategySignal
    confidence: float  # 0.0 to 1.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    quantity: Optional[int] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StrategyPerformance:
    """Strategy performance metrics."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    
    def update_metrics(self):
        """Update calculated metrics."""
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades
        
        if self.losing_trades > 0:
            self.profit_factor = abs(self.average_win * self.winning_trades) / abs(self.average_loss * self.losing_trades)


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""
    
    def __init__(self, config: StrategyConfig, kite_client: KiteClient):
        """Initialize strategy with configuration and Kite client.
        
        Args:
            config: Strategy configuration
            kite_client: Kite API client
        """
        self.config = config
        self.kite_client = kite_client
        self.status = StrategyStatus.STOPPED
        self.positions: Dict[str, Position] = {}
        self.performance = StrategyPerformance()
        self.historical_data: Dict[str, pd.DataFrame] = {}
        self.last_signals: Dict[str, StrategySignalData] = {}
        
    @abstractmethod
    def analyze(self, symbol: str, data: pd.DataFrame) -> StrategySignalData:
        """Analyze market data and generate trading signals.
        
        Args:
            symbol: Trading symbol
            data: Historical OHLC data
            
        Returns:
            Strategy signal with confidence and metadata
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> int:
        """Calculate position size based on risk management rules.
        
        Args:
            symbol: Trading symbol
            entry_price: Planned entry price
            stop_loss: Stop loss price
            
        Returns:
            Position size (quantity)
        """
        pass
    
    def get_historical_data(self, symbol: str, days: int = 100) -> pd.DataFrame:
        """Get historical data for a symbol.
        
        Args:
            symbol: Trading symbol
            days: Number of days of data
            
        Returns:
            DataFrame with OHLC data
        """
        try:
            # Get instrument token (simplified - in real implementation, you'd need to look this up)
            instrument_token = self._get_instrument_token(symbol)
            
            from_date = date.today().replace(day=1)  # Start of current month
            to_date = date.today()
            
            candles = self.kite_client.get_historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=self.config.timeframe
            )
            
            # Convert to DataFrame
            data = []
            for candle in candles:
                data.append({
                    'timestamp': candle.date,
                    'open': candle.open,
                    'high': candle.high,
                    'low': candle.low,
                    'close': candle.close,
                    'volume': candle.volume
                })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
            
            self.historical_data[symbol] = df
            return df
            
        except Exception as e:
            print(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _get_instrument_token(self, symbol: str) -> int:
        """Get instrument token for a symbol.
        
        This is a simplified implementation. In practice, you would:
        1. Cache the instruments list
        2. Search for the symbol
        3. Return the instrument token
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Instrument token
        """
        # Common instrument tokens (you should cache and lookup properly)
        token_map = {
            'RELIANCE': 738561,
            'TCS': 2953217,
            'HDFCBANK': 341249,
            'INFY': 408065,
            'ICICIBANK': 1270529,
            'SBIN': 779521,
            'BHARTIARTL': 2714625,
            'KOTAKBANK': 492033,
            'ITC': 424961,
            'LT': 2939649
        }
        return token_map.get(symbol, 738561)  # Default to RELIANCE
    
    def run_analysis(self) -> Dict[str, StrategySignalData]:
        """Run analysis on all configured symbols.
        
        Returns:
            Dictionary of signals for each symbol
        """
        signals = {}
        
        for symbol in self.config.symbols:
            try:
                # Get fresh data
                data = self.get_historical_data(symbol)
                
                if data.empty:
                    continue
                
                # Analyze and generate signal
                signal = self.analyze(symbol, data)
                signals[symbol] = signal
                self.last_signals[symbol] = signal
                
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
                continue
        
        return signals
    
    def start(self):
        """Start the strategy."""
        self.status = StrategyStatus.ACTIVE
        print(f"Strategy {self.config.name} started")
    
    def stop(self):
        """Stop the strategy."""
        self.status = StrategyStatus.STOPPED
        print(f"Strategy {self.config.name} stopped")
    
    def pause(self):
        """Pause the strategy."""
        self.status = StrategyStatus.PAUSED
        print(f"Strategy {self.config.name} paused")
    
    def resume(self):
        """Resume the strategy."""
        self.status = StrategyStatus.ACTIVE
        print(f"Strategy {self.config.name} resumed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get strategy status and metrics.
        
        Returns:
            Dictionary with strategy status and performance
        """
        return {
            'name': self.config.name,
            'status': self.status.value,
            'symbols': self.config.symbols,
            'total_trades': self.performance.total_trades,
            'win_rate': self.performance.win_rate,
            'total_pnl': self.performance.total_pnl,
            'active_positions': len(self.positions),
            'last_analysis': max([s.timestamp for s in self.last_signals.values()]) if self.last_signals else None
        }


class TechnicalIndicators:
    """Technical analysis indicators for strategies."""
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average."""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average."""
        return data.ewm(span=period).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index."""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """Bollinger Bands."""
        sma = TechnicalIndicators.sma(data, period)
        std = data.rolling(window=period).std()
        
        return {
            'middle': sma,
            'upper': sma + (std * std_dev),
            'lower': sma - (std * std_dev)
        }
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD Indicator."""
        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, pd.Series]:
        """Stochastic Oscillator."""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_percent = k_percent.rolling(window=3).mean()
        
        return {
            'k_percent': k_percent,
            'd_percent': d_percent
        }
