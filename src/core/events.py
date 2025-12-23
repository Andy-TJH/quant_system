from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EventType(str, Enum):
    MARKET = "MARKET"
    SIGNAL = "SIGNAL"
    ORDER = "ORDER"
    FILL = "FILL"
    STATUS = "STATUS"

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class SignalType(str, Enum):
    LONG = "LONG"
    EXIT = "EXIT"

class OrderType(str, Enum):
    MKT = "MKT"
    LMT = "LMT"

class OrderStatus(str, Enum):
    NEW = "NEW"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"

@dataclass(frozen = True, slots = True)
class Event:
    type: EventType
    timestamp_ms: int
    symbol: str

@dataclass(frozen = True, slots = True)
class MarketEvent(Event):
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass(frozen = True, slots = True)
class SignalEvent(Event):
    signal: SignalType
    strength: float = 1.0
    strategy_id: str = "default"

@dataclass(frozen = True, slots = True)
class OrderEvent(Event):
    client_order_id: str
    side: Side
    order_type: OrderType
    qty: int
    limit_price: float = 0.0
    strategy_id: str = "default"

@dataclass(frozen = True, slots = True)
class FillEvent(Event):
    client_order_id: str
    gateway_order_id: str
    side: Side
    fill_qty: int
    fill_price: float
    commission: float = 0.0
    status: OrderStatus = OrderStatus.FILLED


@dataclass(frozen = True, slots = True)
class OrderStatusEvent(Event):
    client_order_id: str
    gateway_order_id: Optional[str]
    status: OrderStatus
    reason: str = ""
    


