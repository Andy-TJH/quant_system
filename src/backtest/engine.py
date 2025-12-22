from __future__ import annotations

from dataclasses import dataclass, field
from queue import SimpleQueue,Empty
from typing import Protocol, Optional, Iterable
from src.data.csv_handler import CSVHandler
from src.utils.logging import setup_logging, get_logger
from src.engine.event_loop import EventLoop

from src.core.events import(
    Event, EventType,
    MarketEvent, SignalEvent, OrderEvent, FillEvent,
    SignalType, Side, OrderType,
)

from src.engine.event_loop import EventLoop
from src.modes.backtest import BacktestMode, BacktestConfig
from src.portfolio.performance_portfolio import PerformancePortfolio
import time

@dataclass
class BacktestConfig:
    flatten_on_end: bool = True
    max_flatten_steps: int = 10

class DataHandler(Protocol):
    def has_next(self) -> bool:
        ...
    def stream_next(self) -> MarketEvent:
        ...

class Strategy(Protocol):
    def on_market(self, event: MarketEvent) -> Optional[SignalEvent]:
        ...

class Portfolio(Protocol):
    def on_signal(self, event: SignalEvent) -> Optional[OrderEvent]:
        ...
    def on_fill(self, event: FillEvent) -> None:
        ...

class ExecutionHandler(Protocol):
    def on_order(self, event: OrderEvent) -> Optional[FillEvent]:
        ...


class DummyDataHandler:
    def __init__(self) -> None:
        self._i = 0
        self._bars = [
            (100.0, 101.0, 99.0, 100.5, 1000.0),
            (100.5, 102.0, 100.0, 101.5, 1200.0),
            (101.5, 101.8, 100.8, 101.0, 900.0),
        ]

    def has_next(self) -> bool:
        return self._i < len(self._bars)
    
    def stream_next(self) -> MarketEvent:
        o, h, l, c, v = self._bars[self._i]
        ts = 1700000000000 + self._i * 60_000
        self._i += 1
        return MarketEvent(
            type=EventType.MARKET,
            timestamp_ms=ts,
            symbol = "TEST",
            open = o, high = h, low = l, close = c, volume = v
        )
    
class DummyStrategy:
    def __init__(self) -> None:
        self._seen = 0
    
    def on_market(self, event: MarketEvent) -> Optional[SignalEvent]:
        self._seen += 1
        if self._seen == 1:
            return SignalEvent(
                type = EventType.SIGNAL,
                timestamp_ms = event.timestamp_ms,
                symbol = event.symbol,
                signal = SignalType.LONG,
                strength = 1.0,
                strategy_id = "dummy"
            )

        if self._seen == 3:
            return SignalEvent(
                type = EventType.SIGNAL,
                timestamp_ms = event.timestamp_ms,
                symbol = event.symbol,
                signal = SignalType.EXIT,
                strength = 1.0,
                strategy_id = "dummy"
            )
        
        return None
    
class DummyPortfolio:
    def __init__(self) -> None:
        self.position = 0
    
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
                strategy_id = event.strategy_id
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
                strategy_id = event.strategy_id
            )
        return None

    def on_fill(self, event: FillEvent) -> None:
        if event.side == Side.BUY:
            self.position += event.fill_qty
        else:
            self.position -= event.fill_qty

@dataclass
class DummyExecution:
    commission: float = 0.0
    fill_price: float = 101.0

    def on_order(self, event: OrderEvent) -> Optional[FillEvent]:
        # MKT 用 self.fill_price；LMT 用 event.limit_price（如果你有）
        price = self.fill_price

        return FillEvent(
            type = EventType.FILL,                 # 或 typec=...
            timestamp_ms = event.timestamp_ms,
            symbol = event.symbol,
            side = event.side,
            fill_qty = event.qty,
            fill_price = price,
            commission = self.commission,

            client_order_id = event.client_order_id,
            gateway_order_id = f"gw-{event.client_order_id}-{int(time.time()*1000)}",
        )
    
@dataclass
class BacktestEngine:
    data: DataHandler
    strategy: Strategy
    portfolio: Portfolio
    execution: ExecutionHandler
    config: BacktestConfig = field(default_factory=BacktestConfig)

    def __post_init__(self) -> None:
        self._last_ts_ms = 0

    def run(self) -> None:
        log = get_logger("backtest.engine")
        log.info("RUN_START")
        loop = EventLoop(
            data=self.data,
            strategy=self.strategy,
            portfolio=self.portfolio,
            execution=self.execution,
        )


        loop.run_until_data_end()

        # 同步 last_ts，给 finalize 用
        self._last_ts_ms = loop.last_ts_ms
        # 复用同一个队列用于 finalize（把 loop.queue 引用过来）
        self._queue = loop.queue  # type: ignore[attr-defined]

        log.info("RUN_DONE final_position=%s", getattr(self.portfolio, "position", None))
        print(f"Done. Final position: {self.portfolio.position}")

def main() -> None:
    setup_logging(level="INFO")
    log = get_logger("backtest")
    log.info("BOOT")

    loop = EventLoop(
        data=CSVHandler(
            csv_path="data/sample_AAPL.csv",
            symbol="AAPL",
        ),
        strategy=DummyStrategy(),
        portfolio = PerformancePortfolio(initial_cash=100_000.0),
        execution=DummyExecution(),
    )
    mode = BacktestMode(
        loop=loop,
        config=BacktestConfig(flatten_on_end=True, max_flatten_steps=10),
    )
    mode.run()

if __name__ == "__main__":
    main()