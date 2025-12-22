from __future__ import annotations
from dataclasses import dataclass, field
from queue import SimpleQueue,Empty
from typing import Protocol, Optional, Iterable
from src.data.csv_handler import CSVHandler
from src.utils.logging import setup_logging, get_logger

from src.core.events import(
    Event, EventType,
    MarketEvent, SignalEvent, OrderEvent, FillEvent,
    SignalType, Side, OrderType,
)

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


class DummyExecution:
    def on_order(self, event: OrderEvent) -> Optional[FillEvent]:
        fill_price = 101.0
        commission = 1.0
        return FillEvent(
            type = EventType.FILL,
            timestamp_ms = event.timestamp_ms,
            symbol = event.symbol,
            client_order_id = event.client_order_id,
            gateway_order_id = f"gid-{event.client_order_id}",
            side = event.side,
            fill_qty = event.qty,
            fill_price = fill_price,
            commission = commission
        )
    
@dataclass
class BacktestEngine:
    data: DataHandler
    strategy: Strategy
    portfolio: Portfolio
    execution: ExecutionHandler
    config: BacktestConfig = field(default_factory=BacktestConfig)

    def __post_init__(self) -> None:
        self._queue: SimpleQueue[Event] = SimpleQueue()

    def run(self) -> None:
        while self.data.has_next():
            market = self.data.stream_next()
            self._last_ts_ms = market.timestamp_ms
            self._queue.put(market)

            while True:
                try:
                    event = self._queue.get_nowait()
                except Empty:
                    break
                except Exception as e:
                    logger.exception("QUEUE_DEAIN_ERROR",)
                    raise

                if event.type == EventType.MARKET:
                    sig = self.strategy.on_market(event)  # type: ignore
                    if sig is not None:
                        self._queue.put(sig)
                
                elif event.type == EventType.SIGNAL:
                    order = self.portfolio.on_signal(event)  # type: ignore
                    if order is not None:
                        self._queue.put(order)
                
                elif event.type == EventType.ORDER:
                    fill = self.execution.on_order(event)  # type: ignore
                    if fill is not None:
                        self._queue.put(fill)
                
                elif event.type == EventType.FILL:
                    self.portfolio.on_fill(event)  # type: ignore
        self._finalize_backtest()
        print(f"Done. Final position: {self.portfolio.position}")


    def _finalize_backtest(self) -> None:
    # 防重入：必须用 try/finally，避免提前 return 导致 _finalizing 永久为 True
        if getattr(self, "_finalizing", False):
            return
        self._finalizing = True
        try:
            if not self.config.flatten_on_end:
                return

            pos = getattr(self.portfolio, "position", 0)
            if pos == 0:
                return

            # 取一个“合理的 symbol”
            symbol = getattr(self.data, "symbol", None) or "UNKNOWN"

            # 用“当前时间戳”作为收口订单的 timestamp_ms（更稳的做法：记录 last_market_ts）
            ts = getattr(self, "_last_ts_ms", 1700000000000)

            # 关键：你的 OrderEvent 字段是 qty，不是 quantity
            side = Side.SELL if pos > 0 else Side.BUY
            qty = abs(pos)

            order = OrderEvent(
                type=EventType.ORDER,
                timestamp_ms=ts,
                symbol=symbol,
                client_order_id=f"finalize-{ts}",
                side=side,
                order_type=OrderType.MKT,
                qty=qty,
                limit_price=0.0,
                strategy_id="finalize",
            )

            self._queue.put(order)

            # drain 队列直到仓位归零
            steps = 0
            while steps < self.config.max_flatten_steps:
                drained_any = False

                while True:
                    try:
                        event = self._queue.get_nowait()
                    except Empty:
                        break

                    drained_any = True

                    if event.type == EventType.MARKET:
                        sig2 = self.strategy.on_market(event)  # type: ignore
                        if sig2 is not None:
                            self._queue.put(sig2)

                    elif event.type == EventType.SIGNAL:
                        order2 = self.portfolio.on_signal(event)  # type: ignore
                        if order2 is not None:
                            self._queue.put(order2)

                    elif event.type == EventType.ORDER:
                        fill = self.execution.on_order(event)  # type: ignore
                        if fill is not None:
                            self._queue.put(fill)

                    elif event.type == EventType.FILL:
                        self.portfolio.on_fill(event)  # type: ignore

                if getattr(self.portfolio, "position", 0) == 0:
                    return
                if not drained_any:
                    break

                steps += 1

            raise RuntimeError(f"Flatten on end failed. Final position={self.portfolio.position}")

        finally:
            self._finalizing = False


def main() -> None:
    setup_logging(level="INFO")
    log = get_logger("backtest")
    log.info("BOOT")
    
    engine = BacktestEngine(
        data = CSVHandler(
            csv_path = "data/sample_AAPL.csv",
            symbol = "AAPL",
        ),
        strategy = DummyStrategy(),
        portfolio = DummyPortfolio(),
        execution = DummyExecution()
    )
    engine.run()
    ##print("Done. Final position:", engine.portfolio.position)


if __name__ == "__main__":
    main()