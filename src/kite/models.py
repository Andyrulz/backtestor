"""Data models for the Kite trading system."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class OrderType(Enum):
    """Order types supported by Kite."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SL_M = "SL-M"


class TransactionType(Enum):
    """Transaction types."""
    BUY = "BUY"
    SELL = "SELL"


class ProductType(Enum):
    """Product types."""
    CNC = "CNC"  # Cash and Carry
    MIS = "MIS"  # Margin Intraday Squareoff
    NRML = "NRML"  # Normal


class Exchange(Enum):
    """Exchanges."""
    NSE = "NSE"
    BSE = "BSE"
    NFO = "NFO"
    BFO = "BFO"
    CDS = "CDS"
    MCX = "MCX"


@dataclass
class OrderRequest:
    """Order placement request."""
    
    tradingsymbol: str
    exchange: Exchange
    transaction_type: TransactionType
    order_type: OrderType
    quantity: int
    product: ProductType
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    validity: str = "DAY"
    disclosed_quantity: Optional[int] = None
    squareoff: Optional[float] = None
    stoploss: Optional[float] = None
    trailing_stoploss: Optional[float] = None
    tag: Optional[str] = None


@dataclass
class Order:
    """Order details."""
    
    order_id: str
    order_timestamp: datetime
    exchange_order_id: Optional[str]
    tradingsymbol: str
    exchange: str
    transaction_type: str
    order_type: str
    product: str
    quantity: int
    price: float
    trigger_price: float
    average_price: float
    pending_quantity: int
    filled_quantity: int
    cancelled_quantity: int
    disclosed_quantity: int
    validity: str
    status: str
    status_message: Optional[str]
    tag: Optional[str]


@dataclass
class Candle:
    """OHLC candle data."""
    
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class Instrument:
    """Trading instrument details."""
    
    instrument_token: int
    exchange_token: int
    tradingsymbol: str
    name: str
    last_price: float
    expiry: Optional[datetime]
    strike: Optional[float]
    tick_size: float
    lot_size: int
    instrument_type: str
    segment: str
    exchange: str


@dataclass
class Position:
    """Position details."""
    
    tradingsymbol: str
    exchange: str
    instrument_token: int
    product: str
    quantity: int
    overnight_quantity: int
    multiplier: int
    average_price: float
    close_price: float
    last_price: float
    value: float
    pnl: float
    m2m: float
    unrealised: float
    realised: float
