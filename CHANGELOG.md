# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased]
### Fixed
- Fixed commission propagation in backtest performance calculation.
  - Ensure `commission` from `ExecutionHandler` is correctly passed to `FillEvent`.
  - Update `PerformanceTracker` to apply commission on both BUY and SELL fills.
  - Record equity updates after fills to avoid stale equity when no subsequent MarketEvent occurs.
  - Prevent false zero PnL for round-trip trades with non-zero commission.

### Tests
- Added regression test to ensure `total_pnl < 0` when per-trade commission is applied
  for a round-trip trade (BUY + SELL) with zero price PnL.
  
### Changed
- Removed legacy `test/` directory and unified all tests under `tests/`.

### Fixed
- Fixed performance summary printing location in BacktestMode (moved from class body into run()).

### Added
- Added DryRun mode (src/modes/dryrun.py).
- Added paper execution handler for simulated fills (src/execution/paper.py).
- Added dryrun entry script (scripts/run_dryrun.py).

### Changed
- EventLoop now optionally forwards market close prices to execution via on_market_price (duck-typed).

### Fixed
- Added public EventLoop.drain() API to support mode-level finalize flatten.

### Added
- Added backtest mode (src/modes/backtest.py) to host flatten logic.

### Changed
- Removed finalize/flatten logic from src/backtest/engine.py and moved it into backtest mode.

### Changed
- Extracted the generic event-driven loop into src/engine/event_loop.py and reused it in backtest engine.

### Added
- Added unified logging module (src/utils/logging.py) with console + file handlers (logs/app.<run_id>.log).

### Changed
- Backtest entrypoint initializes logging and records run lifecycle logs.

### Added
- Introduced CHANGELOG.md to enforce traceable engineering changes.
