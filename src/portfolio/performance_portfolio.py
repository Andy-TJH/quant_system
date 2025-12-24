from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from src.backtest.performance import PerformanceTracker
from src.portfolio.commission import CommissionModel, ZeroCommission, PercentNotionalCommission
from src.core.events import (
    MarketEvent, SignalEvent, OrderEvent, FillEvent,
    EventType, SignalType, Side, OrderType,
)
import logging

@dataclass
class PerformancePortfolio:
    initial_cash: float = 100_000.0
    tracker: PerformanceTracker = field(init=False)
    position: int = 0
    commission_model: CommissionModel = field(default_factory = ZeroCommission)

    def __post_init__(self) -> None:
        self.tracker = PerformanceTracker(initial_cash=self.initial_cash)

    def on_market(self, event: MarketEvent) -> None:
        # mark-to-market using close
        self.tracker.on_market(timestamp_ms=event.timestamp_ms, price=event.close)

    def on_signal(self, event: SignalEvent) -> Optional[OrderEvent]:
        if event.signal == SignalType.LONG and self.position == 0:
            return OrderEvent(
                type = EventType.ORDER,
                timestamp_ms = event.timestamp_ms,
                symbol = event.symbol,
                client_order_id = f"cid-{event.timestamp_ms}",
                side = Side.BUY,
                order_type = OrderType.MKT,
                qty = 10,
                limit_price = 0.0,
                strategy_id = event.strategy_id,
            )

        if event.signal == SignalType.EXIT and self.position != 0:
            return OrderEvent(
                type = EventType.ORDER,
                timestamp_ms = event.timestamp_ms,
                symbol = event.symbol,
                client_order_id = f"cid-{event.timestamp_ms}",
                side = Side.SELL,
                order_type = OrderType.MKT,
                qty = abs(self.position),
                limit_price = 0.0,
                strategy_id = event.strategy_id,
            )
        return None

    def on_fill(self, event: FillEvent) -> None:
        # update position
        if event.side == Side.BUY:
            self.position += event.fill_qty
            side = "BUY"
        else:
            self.position -= event.fill_qty
            side = "SELL"

        commission = float(getattr(event, "commission", 0.0) or 0.0)
        if commission <= 0.0:
            commission = float(self.commission_model.calc(
                symbol = event.symbol,
                qty = int(event.fill_qty),
                price = float(event.fill_price),
                side = event.side,
            ))
            #try:
                #event.commission = commission
            #except Exception:
                #log = logging.getLogger("portfolio.performance")
                #log.warning("SET_EVENT_COMMISSION_FAILED", extra={"commission": commission})

        log = logging.getLogger("portfolio.performance")

        # record performance
        self.tracker.on_fill(
            timestamp_ms = event.timestamp_ms,
            symbol = event.symbol,
            side = side,
            qty = event.fill_qty,
            price = event.fill_price,
            commission = commission,
        )

        #log = logging.getLogger("portfolio.performance")
        
        log.info(
            "PERF_TRACKER_APPLIED_FILL",
            extra={
                "side": side,
                "qty": event.fill_qty,
                "price": event.fill_price,
                "commission": commission,
                "tracker_cash": getattr(self.tracker, "cash", None),
                "tracker_pos": getattr(self.tracker, "position", None),
            },
        )

    def report(self) -> dict:
        return self.tracker.summary()
