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

    def _append_equity_point(self, timestamp_ms: int) -> None:
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
                last_price=self.last_price,
            )
        )

    def on_market(self, timestamp_ms: int, price: float) -> None:
        self.last_price = float(price)
        self._append_equity_point(timestamp_ms=timestamp_ms)

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

        side_u = side.upper()

        # 如果还没有 market price（last_price=0），用成交价兜底
        if self.last_price == 0.0:
            self.last_price = price

        if side_u == "BUY":
            self.position += qty
            self.cash -= qty * price + commission
        else:
            self.position -= qty
            self.cash += qty * price - commission

        self.trades.append(
            TradeRecord(
                timestamp_ms=timestamp_ms,
                symbol=symbol,
                side=side_u,
                qty=qty,
                price=price,
                commission=commission,
            )
        )

        # 关键：成交后也要记录一次 equity，否则 summary 可能拿到成交前的 equity
        self._append_equity_point(timestamp_ms=timestamp_ms)

    def summary(self) -> Dict[str, Any]:
        # 用“最新状态”计算最终权益，避免仅依赖 equity_curve[-1] 的时序问题
        final_equity = self.cash + self.position * self.last_price
        total_pnl = final_equity - self.initial_cash
        total_return = 0.0 if self.initial_cash == 0 else total_pnl / self.initial_cash

        # 可选的一致性检查（放在 return 之前才会生效）
        if len(self.trades) > 0 and self.position == 0 and abs(self.cash - self.initial_cash) < 1e-9:
            raise RuntimeError("PERF_INCONSISTENT_STATE: trades exist but cash and position unchanged.")

        return {
            "initial_cash": self.initial_cash,
            "final_equity": final_equity,
            "total_pnl": total_pnl,
            "total_return": total_return,
            "max_drawdown": self.max_drawdown,
            "trades": len(self.trades),
            "final_position": self.position,
            "last_price": self.last_price,
        }
