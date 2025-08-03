"""Strategy framework for automated trading."""

__version__ = "1.0.0"

from .base import BaseStrategy, StrategySignal, StrategyStatus
from .manager import StrategyManager
from .examples import MovingAverageCrossover, RSIStrategy, BollingerBandsStrategy

__all__ = [
    "BaseStrategy",
    "StrategySignal", 
    "StrategyStatus",
    "StrategyManager",
    "MovingAverageCrossover",
    "RSIStrategy",
    "BollingerBandsStrategy",
]
