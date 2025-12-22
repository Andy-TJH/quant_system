from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict
from src.core.events import (
    EventType, OrderEvent, FillEvent,
    Side,
)
from src.utils.logging import get_logger

@dataclass
class PaperExecutionConfig:
    """
    Paper execution:
    - Fill at last known price (from market data)
    - Simple commission model
    """
    default_commission: float = 1.0

@dataclass
class PaperExecution:
    config: PaperExecutionConfig = PaperExecutionConfig()

    def __post_init__(self) -> None:
        self._log = get_logger("execution.paper")
        self._last_price: Dict[str, float] = {}

    def on_market_price(self, symbol: str, price: float) -> None:
        """Update last known price for symbol (used for paper fills)."""
        self._last_price[symbol] = price

    def on_order(self, event: OrderEvent) -> Optional[FillEvent]:
        """
        For dryrun: assume marketable order, fill immediately at last price.
        """
        symbol = event.symbol
        price = self._last_price.get(symbol)

        if price is None:
            # No price reference => cannot fill
            self._log.warning("PAPER_NO_PRICE symbol=%s cid=%s", symbol, event.client_order_id)
            return None

        fill = FillEvent(
            type=EventType.FILL,
            timestamp_ms=event.timestamp_ms,
            symbol=symbol,
            client_order_id=event.client_order_id,
            gateway_order_id=f"paper-{event.client_order_id}",
            side=event.side,
            fill_qty=event.qty,
            fill_price=price,
            commission=self.config.default_commission,
        )

        self._log.info(
            "PAPER_FILL symbol=%s side=%s qty=%s price=%s commission=%s",
            symbol, event.side, event.qty, price, fill.commission
        )
        return fill
