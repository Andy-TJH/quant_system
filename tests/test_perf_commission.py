from __future__ import annotations

import pytest
from src.engine.event_loop import EventLoop
from src.data.csv_handler import CSVHandler
from src.backtest.engine import DummyStrategy, DummyExecution
from src.backtest.performance import PerformanceTracker
from src.portfolio.performance_portfolio import PerformancePortfolio
from src.modes.backtest import BacktestMode, BacktestConfig

def test_total_pnl_negative_when_commission_applied() -> None:

    loop = EventLoop(
        data=CSVHandler(csv_path="data/sample_AAPL.csv", symbol="AAPL"),
        strategy=DummyStrategy(),
        portfolio=PerformancePortfolio(initial_cash=100_000.0),
        execution=DummyExecution(commission=1.0),  # 手续费打开
    )

    # 用真实入口跑（别用 loop.run）
    mode = BacktestMode(loop=loop, config=BacktestConfig(flatten_on_end=True))
    mode.run()

    summary = loop.portfolio.report()  # type: ignore[attr-defined]
    assert summary["trades"] >= 2
    assert summary["total_commission"] == 2.0
    assert summary["total_pnl"] == -2.0


def test_total_commission_and_pnl_match_per_trade_commission() -> None:
    """
    当前实现是每笔固定手续费（FillEvent.commission = self.commission），没有 rate/min_fee。
    目标：防止手续费链路断掉导致 total_pnl 回到 0。
    """
    per_trade_commission = 1.0

    loop = EventLoop(
        data=CSVHandler(csv_path="data/sample_AAPL.csv", symbol="AAPL"),
        strategy=DummyStrategy(),
        portfolio=PerformancePortfolio(initial_cash=100_000),
        execution=DummyExecution(commission=per_trade_commission),
    )

    mode = BacktestMode(loop=loop, config=BacktestConfig(flatten_on_end=True))
    mode.run()

    summary = loop.portfolio.report()  # type: ignore[attr-defined]

    assert summary["trades"] >= 2
    assert summary["total_commission"] == summary["trades"] * per_trade_commission
    assert summary["total_pnl"] == -summary["total_commission"]



def test_total_commission_is_two_times_per_trade_commission():
    loop = EventLoop(
        data=CSVHandler(csv_path="data/sample_AAPL.csv", symbol="AAPL"),
        strategy=DummyStrategy(),
        portfolio=PerformancePortfolio(initial_cash=100_000),
        execution=DummyExecution(commission=1.0),  # 每笔固定 1.0
    )

    mode = BacktestMode(loop=loop, config=BacktestConfig(flatten_on_end=True))
    mode.run()

    summary = loop.portfolio.report()  # type: ignore[attr-defined]

    c = 1.0
    assert summary["total_commission"] == summary["trades"] * c
    assert summary["total_pnl"] == -summary["total_commission"]


