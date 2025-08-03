"""Strategy manager for handling multiple trading strategies."""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd

from .base import BaseStrategy, StrategyStatus, StrategySignalData, StrategySignal
from kite.client import KiteClient
from kite.models import OrderRequest, OrderType, TransactionType, ProductType, Exchange

logger = logging.getLogger(__name__)


@dataclass
class StrategyExecution:
    """Track strategy execution details."""
    strategy_name: str
    symbol: str
    signal: StrategySignalData
    order_id: Optional[str] = None
    executed_price: Optional[float] = None
    execution_time: Optional[datetime] = None
    status: str = "PENDING"


class StrategyManager:
    """Manages multiple trading strategies and their execution."""
    
    def __init__(self, kite_client: KiteClient):
        """Initialize strategy manager.
        
        Args:
            kite_client: Kite API client
        """
        self.kite_client = kite_client
        self.strategies: Dict[str, BaseStrategy] = {}
        self.is_running = False
        self.execution_thread: Optional[threading.Thread] = None
        self.executions: List[StrategyExecution] = []
        self.auto_execute = False
        self.execution_interval = 60  # seconds
        
    def add_strategy(self, strategy: BaseStrategy) -> None:
        """Add a strategy to the manager.
        
        Args:
            strategy: Strategy instance to add
        """
        self.strategies[strategy.config.name] = strategy
        logger.info(f"Added strategy: {strategy.config.name}")
    
    def remove_strategy(self, strategy_name: str) -> bool:
        """Remove a strategy from the manager.
        
        Args:
            strategy_name: Name of strategy to remove
            
        Returns:
            True if strategy was removed, False if not found
        """
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            strategy.stop()
            del self.strategies[strategy_name]
            logger.info(f"Removed strategy: {strategy_name}")
            return True
        return False
    
    def start_strategy(self, strategy_name: str) -> bool:
        """Start a specific strategy.
        
        Args:
            strategy_name: Name of strategy to start
            
        Returns:
            True if started successfully
        """
        if strategy_name in self.strategies:
            self.strategies[strategy_name].start()
            return True
        return False
    
    def stop_strategy(self, strategy_name: str) -> bool:
        """Stop a specific strategy.
        
        Args:
            strategy_name: Name of strategy to stop
            
        Returns:
            True if stopped successfully
        """
        if strategy_name in self.strategies:
            self.strategies[strategy_name].stop()
            return True
        return False
    
    def start_all_strategies(self) -> None:
        """Start all strategies."""
        for strategy in self.strategies.values():
            if strategy.config.enabled:
                strategy.start()
        
        # Start the main execution loop
        self.is_running = True
        if self.execution_thread is None or not self.execution_thread.is_alive():
            self.execution_thread = threading.Thread(target=self._execution_loop, daemon=True)
            self.execution_thread.start()
        
        logger.info("Started all strategies")
    
    def stop_all_strategies(self) -> None:
        """Stop all strategies."""
        self.is_running = False
        
        for strategy in self.strategies.values():
            strategy.stop()
        
        logger.info("Stopped all strategies")
    
    def run_analysis_cycle(self) -> Dict[str, Dict[str, StrategySignalData]]:
        """Run analysis cycle for all active strategies.
        
        Returns:
            Dictionary of signals for each strategy and symbol
        """
        all_signals = {}
        
        for strategy_name, strategy in self.strategies.items():
            if strategy.status == StrategyStatus.ACTIVE:
                try:
                    signals = strategy.run_analysis()
                    all_signals[strategy_name] = signals
                    
                    # Log significant signals
                    for symbol, signal in signals.items():
                        if signal.signal in [StrategySignal.BUY, StrategySignal.SELL]:
                            logger.info(f"{strategy_name} - {symbol}: {signal.signal.value} "
                                      f"(confidence: {signal.confidence:.2f})")
                    
                except Exception as e:
                    logger.error(f"Error running analysis for {strategy_name}: {e}")
                    strategy.status = StrategyStatus.ERROR
        
        return all_signals
    
    def execute_signals(self, signals: Dict[str, Dict[str, StrategySignalData]], 
                       dry_run: bool = True) -> List[StrategyExecution]:
        """Execute trading signals.
        
        Args:
            signals: Dictionary of signals from strategies
            dry_run: If True, only log what would be executed
            
        Returns:
            List of execution results
        """
        executions = []
        
        for strategy_name, strategy_signals in signals.items():
            strategy = self.strategies[strategy_name]
            
            for symbol, signal in strategy_signals.items():
                if signal.signal in [StrategySignal.BUY, StrategySignal.SELL]:
                    execution = self._execute_signal(strategy, signal, dry_run)
                    executions.append(execution)
        
        return executions
    
    def _execute_signal(self, strategy: BaseStrategy, signal: StrategySignalData, 
                       dry_run: bool = True) -> StrategyExecution:
        """Execute a single trading signal.
        
        Args:
            strategy: Strategy instance
            signal: Signal to execute
            dry_run: If True, only simulate execution
            
        Returns:
            Execution result
        """
        execution = StrategyExecution(
            strategy_name=strategy.config.name,
            symbol=signal.symbol,
            signal=signal
        )
        
        try:
            # Calculate position size
            entry_price = signal.entry_price or self._get_current_price(signal.symbol)
            stop_loss = signal.stop_loss or entry_price * (1 - strategy.config.stop_loss_pct)
            
            quantity = strategy.calculate_position_size(signal.symbol, entry_price, stop_loss)
            
            if dry_run:
                execution.status = "DRY_RUN"
                execution.executed_price = entry_price
                execution.execution_time = datetime.now()
                logger.info(f"DRY RUN - {strategy.config.name}: {signal.signal.value} "
                          f"{quantity} {signal.symbol} @ {entry_price:.2f}")
            else:
                # Create and place order
                order_request = OrderRequest(
                    tradingsymbol=signal.symbol,
                    exchange=Exchange.NSE,  # Adjust based on symbol
                    transaction_type=TransactionType.BUY if signal.signal == StrategySignal.BUY else TransactionType.SELL,
                    order_type=OrderType.MARKET,  # Can be enhanced to use limit orders
                    quantity=quantity,
                    product=ProductType.MIS,  # Intraday by default
                    tag=f"{strategy.config.name}_auto"
                )
                
                order_id = self.kite_client.place_order(order_request)
                execution.order_id = order_id
                execution.status = "EXECUTED"
                execution.execution_time = datetime.now()
                
                logger.info(f"EXECUTED - {strategy.config.name}: {signal.signal.value} "
                          f"{quantity} {signal.symbol} - Order ID: {order_id}")
        
        except Exception as e:
            execution.status = "ERROR"
            logger.error(f"Error executing signal for {signal.symbol}: {e}")
        
        self.executions.append(execution)
        return execution
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Current price (simplified implementation)
        """
        # This is a simplified implementation
        # In practice, you would get real-time quotes
        try:
            # Use a strategy's historical data method to get recent price
            for strategy in self.strategies.values():
                if symbol in strategy.config.symbols:
                    data = strategy.get_historical_data(symbol, days=1)
                    if not data.empty:
                        return float(data['close'].iloc[-1])
            
            # Fallback
            return 100.0
            
        except Exception:
            return 100.0  # Default fallback price
    
    def _execution_loop(self) -> None:
        """Main execution loop running in background."""
        logger.info("Strategy execution loop started")
        
        while self.is_running:
            try:
                # Run analysis cycle
                signals = self.run_analysis_cycle()
                
                # Execute signals if auto_execute is enabled
                if self.auto_execute and signals:
                    self.execute_signals(signals, dry_run=False)
                
                # Wait for next cycle
                time.sleep(self.execution_interval)
                
            except Exception as e:
                logger.error(f"Error in execution loop: {e}")
                time.sleep(10)  # Wait before retrying
        
        logger.info("Strategy execution loop stopped")
    
    def get_all_signals(self) -> Dict[str, Dict[str, StrategySignalData]]:
        """Get latest signals from all strategies.
        
        Returns:
            Dictionary of latest signals
        """
        all_signals = {}
        
        for strategy_name, strategy in self.strategies.items():
            if strategy.last_signals:
                all_signals[strategy_name] = strategy.last_signals.copy()
        
        return all_signals
    
    def get_strategy_status(self) -> List[Dict[str, Any]]:
        """Get status of all strategies.
        
        Returns:
            List of strategy status dictionaries
        """
        status_list = []
        
        for strategy in self.strategies.values():
            status_list.append(strategy.get_status())
        
        return status_list
    
    def get_recent_executions(self, limit: int = 50) -> List[StrategyExecution]:
        """Get recent executions.
        
        Args:
            limit: Maximum number of executions to return
            
        Returns:
            List of recent executions
        """
        return sorted(self.executions, 
                     key=lambda x: x.execution_time or datetime.min, 
                     reverse=True)[:limit]
    
    def set_auto_execute(self, enabled: bool) -> None:
        """Enable or disable automatic execution of signals.
        
        Args:
            enabled: Whether to enable auto execution
        """
        self.auto_execute = enabled
        logger.info(f"Auto execution {'enabled' if enabled else 'disabled'}")
    
    def set_execution_interval(self, seconds: int) -> None:
        """Set the execution interval for the main loop.
        
        Args:
            seconds: Interval in seconds between execution cycles
        """
        self.execution_interval = max(30, seconds)  # Minimum 30 seconds
        logger.info(f"Execution interval set to {self.execution_interval} seconds")
    
    def emergency_stop(self) -> None:
        """Emergency stop all strategies and cancel pending orders."""
        logger.warning("EMERGENCY STOP initiated")
        
        # Stop all strategies
        self.stop_all_strategies()
        
        # Cancel all pending orders (if you want to implement this)
        try:
            orders = self.kite_client.get_orders()
            for order in orders:
                if order.status in ["OPEN", "PENDING"]:
                    try:
                        self.kite_client.cancel_order(order.order_id)
                        logger.info(f"Cancelled order: {order.order_id}")
                    except Exception as e:
                        logger.error(f"Error cancelling order {order.order_id}: {e}")
        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
        
        logger.warning("Emergency stop completed")
