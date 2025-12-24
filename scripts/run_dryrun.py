from __future__ import annotations

from src.utils.logging import setup_logging, get_logger
from src.data.csv_handler import CSVHandler
from src.engine.event_loop import EventLoop
from src.modes.dryrun import DryRunMode, DryRunConfig
from src.execution.paper import PaperExecution, PaperExecutionConfig
# 过渡期：你 DummyStrategy/DummyPortfolio 在 src/backtest/engine.py 里
from src.backtest.engine import DummyStrategy, DummyPortfolio

def main() -> None:
    setup_logging(level="INFO")
    log = get_logger("scripts.run_dryrun")
    log.info("BOOT")

    data = CSVHandler(csv_path="data/sample_AAPL.csv", symbol="AAPL")
    strategy = DummyStrategy()
    portfolio = DummyPortfolio()
    execution = PaperExecution(PaperExecutionConfig(default_commission=1.0))

    loop = EventLoop(
        data=data,
        strategy=strategy,
        portfolio=portfolio,
        execution=execution,
    )

    mode = DryRunMode(loop=loop, config=DryRunConfig(emit_summary=True))
    mode.run()

if __name__ == "__main__":
    main()
