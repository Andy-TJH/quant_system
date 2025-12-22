# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased]
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
