from __future__ import annotations

def test_total_pnl_negative_when_commission_applied() -> None:
    """
    When per-trade commission is non-zero, total_pnl must be negative
    for a round-trip (BUY + SELL) even if price PnL is 0.
    """
    from src.engine.event_loop import EventLoop
    from src.data.csv_handler import CSVHandler
    from src.backtest.engine import DummyStrategy, DummyExecution
    from src.portfolio.performance_portfolio import PerformancePortfolio
    from src.modes.backtest import BacktestMode, BacktestConfig

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
