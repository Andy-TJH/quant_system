from __future__ import annotations

from dataclasses import dataclass, field
from queue import SimpleQueue, Empty
from typing import Optional

from src.core.events import (
    Event, EventType,
    MarketEvent, SignalEvent, OrderEvent, FillEvent,
)

from src.utils.logging import get_logger

class DataHandler:
    def has_next(self) -> bool: ...
    def stream_next(self) -> MarketEvent: ...

class Strategy:
    def on_market(self, event: MarketEvent) -> Optional[SignalEvent]: ...

class Portfolio:
    def on_signal(self, event: SignalEvent) -> Optional[OrderEvent]: ...
    def on_fill(self, event: FillEvent) -> None: ...

class ExecutionHandler:
    def on_order(self, event: OrderEvent) -> Optional[FillEvent]: ...

@dataclass
class EventLoop:
    data: DataHandler
    strategy: Strategy
    portfolio: Portfolio
    execution: ExecutionHandler
    queue: SimpleQueue[Event] = field(default_factory=SimpleQueue)
    last_ts_ms: int = 0

    def run_until_data_end(self) -> None:
        """
        通用事件循环：拉取 MarketEvent -> 入队 -> drain queue。
        不处理“回测收口/平仓”等策略性行为。
        """
        log = get_logger(self.__class__.__name__)
        log.info("ENGINE_START")

        while self.data.has_next():
            market = self.data.stream_next()
            self.last_ts_ms = market.timestamp_ms
            self.queue.put(market)

            self._drain_queue()

        log.info("ENGINE_END")

    def _drain_queue(self) -> None:
        log = get_logger(self.__class__.__name__)

        while True:
            try:
                event = self.queue.get_nowait()
            except Empty:
                break

            et = event.type

            if et == EventType.MARKET:
                if hasattr(self.execution, "on_market_price"):
                    try:
                        self.execution.on_market_price(event.symbol, event.close) # type: ignore
                    except Exception as e:
                        log.warning("EXECUTION_ON_MARKET_PRICE_FAILED")
                        raise

                if hasattr(self.portfolio, "on_market"):
                    self.portfolio.on_market(event)  
    
                sig = self.strategy.on_market(event)  # type: ignore

                if sig is not None:
                    log.info("SIGNAL_EMIT", extra={"symbol": getattr(sig, "symbol", None), "signal": getattr(sig, "signal", None)})
                    self.queue.put(sig)

            elif et == EventType.SIGNAL:
                order = self.portfolio.on_signal(event)  # type: ignore
                if order is not None:
                    log.info("ORDER_EMIT", extra={"symbol": getattr(order, "symbol", None), "side": getattr(order, "side", None), "qty": getattr(order, "qty", None)})
                    self.queue.put(order)

            elif et == EventType.ORDER:
                fill = self.execution.on_order(event)  # type: ignore
                if fill is not None:
                    log.info("FILL_EMIT", extra={"symbol": getattr(fill, "symbol", None), "side": getattr(fill, "side", None), "qty": getattr(fill, "fill_qty", None)})
                    self.queue.put(fill)

            elif et == EventType.FILL:
                self.portfolio.on_fill(event)  # type: ignore
                log.info("PORTFOLIO_APPLY_FILL", extra={"symbol": getattr(event, "symbol", None)})

            else:
                log.warning("UNKNOWN_EVENT", extra={"event_type": str(et)})

    def drain(self) -> None:
        self._drain_queue()

