from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional

class CommissionModel(Protocol):
    def calc(self, *, symbol: str, qty: int, price: float, side: object) -> float:
        """Return commission for this fill. Must be >= 0."""
        ...

@dataclass(frozen=True)
class ZeroCommission:
    def calc(self, *, symbol: str, qty: int, price: float, side: object) -> float:
        return 0.0

@dataclass(frozen=True)
class PercentNotionalCommission:
    """
    Commission = max(min_fee, min(max_fee, notional * rate))
    - rate: e.g. 0.0003 means 0.03% (3 bps)
    - min_fee/max_fee: in cash currency
    """
    rate: float = 0.0
    min_fee: float = 0.0
    max_fee: Optional[float] = None

    def calc(self, *, symbol: str, qty: int, price: float, side: object) -> float:
        notional = float(qty) * float(price)
        fee = notional * float(self.rate)

        if fee < self.min_fee:
            fee = self.min_fee
        if self.max_fee is not None and fee > self.max_fee:
            fee = self.max_fee

        # Guard
        if fee < 0:
            fee = 0.0
        return float(fee)
