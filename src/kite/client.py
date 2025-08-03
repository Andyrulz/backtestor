"""Kite API client wrapper with enhanced functionality."""

import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from kiteconnect import KiteConnect
from kite.models import (
    OrderRequest,
    Order,
    Candle,
    Instrument,
    Position,
    OrderType,
    TransactionType,
    ProductType,
    Exchange,
)

logger = logging.getLogger(__name__)


class KiteClient:
    """Enhanced Kite API client with type safety and error handling."""
    
    def __init__(self, api_key: str, access_token: str, api_secret: str = ""):
        """Initialize the Kite client.
        
        Args:
            api_key: Kite API key
            access_token: Access token for API authentication
            api_secret: API secret (optional, for token generation)
        """
        self.api_key = api_key
        self.access_token = access_token
        self.api_secret = api_secret
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        
        logger.info("Kite client initialized successfully")
    
    def place_order(self, order_request: OrderRequest) -> str:
        """Place an order.
        
        Args:
            order_request: Order details
            
        Returns:
            Order ID
            
        Raises:
            Exception: If order placement fails
        """
        try:
            order_params = {
                "variety": order_request.variety.value,
                "tradingsymbol": order_request.tradingsymbol,
                "exchange": order_request.exchange.value,
                "transaction_type": order_request.transaction_type.value,
                "order_type": order_request.order_type.value,
                "quantity": order_request.quantity,
                "product": order_request.product.value,
                "validity": order_request.validity,
            }
            
            # Add optional parameters
            if order_request.price is not None:
                order_params["price"] = order_request.price
            if order_request.trigger_price is not None:
                order_params["trigger_price"] = order_request.trigger_price
            if order_request.disclosed_quantity is not None:
                order_params["disclosed_quantity"] = order_request.disclosed_quantity
            if order_request.tag is not None:
                order_params["tag"] = order_request.tag
                
            logger.info(f"Placing order with params: {order_params}")
            response = self.kite.place_order(**order_params)
            logger.info(f"API response: {response} (type: {type(response)})")
            
            # Handle different response formats
            if isinstance(response, dict):
                order_id = response.get("order_id", str(response))
            else:
                # Response might be just the order ID as a string
                order_id = str(response)
            
            logger.info(f"Order placed successfully: {order_id}")
            return order_id
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            if 'order_params' in locals():
                logger.error(f"Order params: {order_params}")
            raise Exception(f"Order placement failed: {str(e)}")
    
    def get_orders(self) -> List[Order]:
        """Get all orders for the day.
        
        Returns:
            List of orders
        """
        try:
            orders_data = self.kite.orders()
            orders = []
            
            for order_data in orders_data:
                # Handle order_timestamp - could be string or datetime
                order_timestamp = order_data["order_timestamp"]
                if isinstance(order_timestamp, str):
                    order_timestamp = datetime.strptime(order_timestamp, "%Y-%m-%d %H:%M:%S")
                elif not isinstance(order_timestamp, datetime):
                    # If it's neither string nor datetime, convert to datetime
                    order_timestamp = datetime.now()
                
                order = Order(
                    order_id=order_data["order_id"],
                    order_timestamp=order_timestamp,
                    exchange_order_id=order_data.get("exchange_order_id"),
                    tradingsymbol=order_data["tradingsymbol"],
                    exchange=order_data["exchange"],
                    transaction_type=order_data["transaction_type"],
                    order_type=order_data["order_type"],
                    product=order_data["product"],
                    quantity=order_data["quantity"],
                    price=order_data["price"],
                    trigger_price=order_data["trigger_price"],
                    average_price=order_data["average_price"],
                    pending_quantity=order_data["pending_quantity"],
                    filled_quantity=order_data["filled_quantity"],
                    cancelled_quantity=order_data["cancelled_quantity"],
                    disclosed_quantity=order_data["disclosed_quantity"],
                    validity=order_data["validity"],
                    status=order_data["status"],
                    status_message=order_data.get("status_message"),
                    tag=order_data.get("tag"),
                )
                orders.append(order)
            
            logger.info(f"Retrieved {len(orders)} orders")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise
    
    def cancel_order(self, order_id: str, variety: str = "regular") -> str:
        """Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            variety: Order variety (default: regular)
            
        Returns:
            Order ID of cancelled order
        """
        try:
            response = self.kite.cancel_order(variety=variety, order_id=order_id)
            logger.info(f"Order cancelled successfully: {order_id}")
            return response["order_id"]
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    def get_historical_data(
        self,
        instrument_token: int,
        from_date: date,
        to_date: date,
        interval: str = "day",
        continuous: bool = False,
        oi: bool = False,
    ) -> List[Candle]:
        """Get historical candlestick data.
        
        Args:
            instrument_token: Instrument token
            from_date: Start date
            to_date: End date
            interval: Candle interval (minute, day, etc.)
            continuous: Continuous contract (for futures)
            oi: Include open interest
            
        Returns:
            List of candles
        """
        try:
            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval,
                continuous=continuous,
                oi=oi,
            )
            
            candles = []
            for candle_data in data:
                candle = Candle(
                    date=candle_data["date"],
                    open=candle_data["open"],
                    high=candle_data["high"],
                    low=candle_data["low"],
                    close=candle_data["close"],
                    volume=candle_data["volume"],
                )
                candles.append(candle)
            
            logger.info(f"Retrieved {len(candles)} candles for token {instrument_token}")
            return candles
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            raise
    
    def get_instruments(self, exchange: Optional[str] = None) -> List[Instrument]:
        """Get trading instruments.
        
        Args:
            exchange: Exchange to filter by (optional)
            
        Returns:
            List of instruments
        """
        try:
            instruments_data = self.kite.instruments(exchange=exchange)
            instruments = []
            
            for instrument_data in instruments_data:
                # Handle expiry date parsing
                expiry = None
                if instrument_data.get("expiry"):
                    try:
                        expiry = datetime.strptime(instrument_data["expiry"], "%Y-%m-%d").date()
                    except ValueError:
                        pass  # Skip invalid dates
                
                instrument = Instrument(
                    instrument_token=instrument_data["instrument_token"],
                    exchange_token=instrument_data["exchange_token"],
                    tradingsymbol=instrument_data["tradingsymbol"],
                    name=instrument_data["name"],
                    last_price=instrument_data.get("last_price", 0.0),
                    expiry=expiry,
                    strike=instrument_data.get("strike"),
                    tick_size=instrument_data["tick_size"],
                    lot_size=instrument_data["lot_size"],
                    instrument_type=instrument_data["instrument_type"],
                    segment=instrument_data["segment"],
                    exchange=instrument_data["exchange"],
                )
                instruments.append(instrument)
            
            logger.info(f"Retrieved {len(instruments)} instruments")
            return instruments
            
        except Exception as e:
            logger.error(f"Failed to get instruments: {e}")
            raise
    
    def get_positions(self) -> List[Position]:
        """Get current positions.
        
        Returns:
            List of positions
        """
        try:
            positions_data = self.kite.positions()
            positions = []
            
            # Combine day and net positions
            all_positions = positions_data.get("day", []) + positions_data.get("net", [])
            
            for position_data in all_positions:
                position = Position(
                    tradingsymbol=position_data["tradingsymbol"],
                    exchange=position_data["exchange"],
                    instrument_token=position_data["instrument_token"],
                    product=position_data["product"],
                    quantity=position_data["quantity"],
                    overnight_quantity=position_data["overnight_quantity"],
                    multiplier=position_data["multiplier"],
                    average_price=position_data["average_price"],
                    close_price=position_data["close_price"],
                    last_price=position_data["last_price"],
                    value=position_data["value"],
                    pnl=position_data["pnl"],
                    m2m=position_data["m2m"],
                    unrealised=position_data["unrealised"],
                    realised=position_data["realised"],
                )
                positions.append(position)
            
            logger.info(f"Retrieved {len(positions)} positions")
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise
    
    def get_margins(self) -> Dict[str, Any]:
        """Get account margins.
        
        Returns:
            Margin details
        """
        try:
            margins = self.kite.margins()
            logger.info("Retrieved margin information")
            return margins
            
        except Exception as e:
            logger.error(f"Failed to get margins: {e}")
            raise
    
    def get_profile(self) -> Dict[str, Any]:
        """Get user profile.
        
        Returns:
            User profile information
        """
        try:
            profile = self.kite.profile()
            logger.info("Retrieved user profile")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get profile: {e}")
            raise
