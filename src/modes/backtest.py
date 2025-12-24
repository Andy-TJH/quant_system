from __future__ import annotations

from dataclasses import dataclass, field
from queue import Empty
from src.core.events import (
    EventType, OrderEvent,
    Side, OrderType,
)
from src.engine.event_loop import EventLoop
from src.utils.logging import get_logger
import logging

log = logging.getLogger("mode.backtest")

@dataclass
class BacktestConfig:
    flatten_on_end: bool = True
    max_flatten_steps: int = 10

@dataclass
class BacktestMode:
    loop: EventLoop
    config: BacktestConfig = field(default_factory=BacktestConfig)

    def run(self) -> None:
        log = get_logger("mode.backtest")
        log.info("BACKTEST_START")

        self.loop.run_until_data_end()
        self._finalize_flatten()

        pos = getattr(self.loop.portfolio, "position", 0)
        log.info("BACKTEST_DONE final_position=%s", pos)
        print(f"Done. Final position: {pos}")

        if hasattr(self.loop.portfolio, "report"):
            summary = self.loop.portfolio.report()  # type: ignore[attr-defined]

        log.info("PERF_SUMMARY %s", summary)

    def _finalize_flatten(self) -> None:
        log = get_logger("mode.backtest")

        if not self.config.flatten_on_end:
            log.info("FLATTEN_SKIP disabled")
            return

        pos = getattr(self.loop.portfolio, "position", 0)
        if pos == 0:
            log.info("FLATTEN_SKIP position=0")
            return

        ts = self.loop.last_ts_ms
        symbol = getattr(self.loop.data, "symbol", "UNKNOWN")
        side = Side.SELL if pos > 0 else Side.BUY

        order = OrderEvent(
            type=EventType.ORDER,
            timestamp_ms=ts,
            symbol=symbol,
            client_order_id=f"flatten-{ts}",
            side=side,
            order_type=OrderType.MKT,
            qty=abs(pos),
            limit_price=0.0,
            strategy_id="finalize",
        )

        log.info("FLATTEN_START symbol=%s side=%s qty=%s", symbol, side, abs(pos))
        self.loop.queue.put(order)

        steps = 0
        while steps < self.config.max_flatten_steps:
            drained = False
            while True:
                try:
                    event = self.loop.queue.get_nowait()
                except Empty:
                    break
                else:
                    self.loop.queue.put(event)
                    drained = True
                    self.loop.drain()

            if getattr(self.loop.portfolio, "position", 0) == 0:
                log.info("FLATTEN_OK")
                return

            if not drained:
                break

            steps += 1

        raise RuntimeError(
            f"Flatten failed, final position={getattr(self.loop.portfolio, 'position', None)}"
        )
