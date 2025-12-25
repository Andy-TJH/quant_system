from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class EquityPoint:
    timestamp_ms: int
    equity: float
    cash: float
    position: int
    last_price: float

@dataclass
class TradeRecord:
    timestamp_ms: int
    symbol: str
    side: str  # "BUY" or "SELL"
    qty: int
    price: float
    commission: float

@dataclass
class PerformanceTracker:
    initial_cash: float = 100_000.0

    cash: float = field(init=False)
    position: int = field(init=False, default=0)
    last_price: float = field(init=False, default=0.0)

    equity_curve: List[EquityPoint] = field(init=False, default_factory=list)
    trades: List[TradeRecord] = field(init=False, default_factory=list)

    peak_equity: float = field(init=False)
    max_drawdown: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self.cash = float(self.initial_cash)
        self.peak_equity = float(self.initial_cash)

    def _mark_to_market(self, timestamp_ms: int, price: float) -> None:
        """内部统一的 mark-to-market：写 equity_curve、更新回撤等。"""
        self.last_price = float(price)
        equity = self.cash + self.position * self.last_price

        if equity > self.peak_equity:
            self.peak_equity = equity

        dd = 0.0 if self.peak_equity == 0 else (self.peak_equity - equity) / self.peak_equity
        if dd > self.max_drawdown:
            self.max_drawdown = dd

        self.equity_curve.append(
            EquityPoint(
                timestamp_ms=timestamp_ms,
                equity=equity,
                cash=self.cash,
                position=self.position,
                last_price=float(price),
            )
        )

    def on_market(self, timestamp_ms: int, price: float) -> None:
        self.last_price = float(price)
        self._mark_to_market(timestamp_ms, price)

    def on_fill(
        self,
        timestamp_ms: int,
        symbol: str,
        side: str,
        qty: int,
        price: float,
        commission: float,
    ) -> None:
        
        qty = int(qty)
        price = float(price)
        commission = float(commission)

        s = side.upper()
        if s == "BUY":
            self.position += qty
            self.cash -= qty * price + commission
        elif s == "SELL":
            self.position -= qty
            self.cash += qty * price - commission
        else:
            raise ValueError(f"Unknown side: {side}")

        self.trades.append(
            TradeRecord(
                timestamp_ms=timestamp_ms,
                symbol=symbol,
                side=s,
                qty=qty,
                price=price,
                commission=commission,
            )
        )
        mtm_price = float(price) if price else float(getattr(self, "last_price", 0.0))
        self._mark_to_market(timestamp_ms, mtm_price)

    def summary(self) -> Dict[str, Any]:
        last_equity = self.equity_curve[-1].equity if self.equity_curve else float(self.initial_cash)
        total_pnl = last_equity - self.initial_cash
        total_return = 0.0 if self.initial_cash == 0 else total_pnl / self.initial_cash
        total_commission = sum(t.commission for t in self.trades)

        out = {
            "initial_cash": self.initial_cash,
            "final_equity": last_equity,
            "total_pnl": total_pnl,
            "total_return": total_return,
            "max_drawdown": self.max_drawdown,
            "trades": len(self.trades),
            "final_position": self.position,
            "last_price": float(self.equity_curve[-1].last_price) if self.equity_curve else 0.0,
            "total_commission": total_commission,
            "cash": self.cash,  # 方便排查
        }

        eps = 1e-9
        if total_commission > 0 and abs(self.cash - self.initial_cash) < eps:
            raise RuntimeError(
                "PERF_INCONSISTENT_STATE: commission>0 but cash unchanged. "
                "Commission may not be propagated into fills/portfolio."
            )

        return out