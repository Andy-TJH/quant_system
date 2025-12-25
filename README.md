# Quant System
A modular, event-driven quantitative trading system with backtesting support,
designed for engineering clarity, extensibility, and real-world trading workflows.

## Overview
Quant System is a Python-based quantitative trading framework built with an event-driven architecture.

### The project focuses on:
- Clear separation of concerns (data/strategy/execution/portfolio)
- Config-driven runs (YAML)
- Backtesting first, with future extension to paper trading and live trading
- Engineering practices aligned with real-world trading systems

### This repository is intended both as:
- a personal research & trading system, and a demonstration of engineering capability for quantitative/backend/test-development roles.

## Key Features
- Event-driven backtest engine
- Modular strategy interface
- Commission & slippage modeling
- Self-contained demo configuration (no external data dependency)
- Pytest-based unit testing
- Git workflow aligned with real engineering teams (feature branches, PRs)

## Quick Start
### 1. Environment Setup
python -m venv .venv

- Windows (PowerShell)
. .\.venv\Scripts\Activate.ps1

- macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

### 2. Run Demo Backtest (Self-contained)
The demo configuration does not rely on external APIs (e.g. Tushare).
All required data is stored inside the repository.

- python -m src.backtest.engine --config configs/demo.yaml

#### This will run a minimal backtest using:
- local CSV price data
- a simple example strategy
- fixed commission & slippage model

### 3. Run Tests
- pytest

## Configuration System
All runs are driven by YAML configuration files under configs/.

### Top-level Config Semantics
- Each config file follows the same structure:

run:        # runtime behavior (seed, flatten rules, etc.)
data:       # data source configuration
strategy:   # strategy name & parameters
engine:     # capital, commission, slippage, execution settings

### Available Configs
File & Description
configs/demo.yaml__Self-contained demo config (recommended entry point)
configs/backtest.yaml__Backtest preset (WIP)
configs/dryrun.yaml__Paper trading preset (WIP)
configs/live.yaml	Live__trading preset (WIP)


## Repository Structure
quant_system/
├── src/
│   ├── backtest/        # backtest engine & core loop
│   ├── core/            # event definitions & enums
│   ├── execution/       # execution & commission models
│   └── data/            # data handlers
│
├── tests/               # pytest unit tests
├── configs/             # YAML run configurations
├── data/                # demo / sample datasets (repo-local)
│
├── README.md
├── requirements.txt
└── .gitignore

## Design Philosophy
- Event-driven: MarketEvent → SignalEvent → OrderEvent → FillEvent
- Config-first: behavior changes through YAML, not hardcoded logic
- Backtest correctness over speed (optimization comes later)
- Engineering realism: explicit commissions, slippage, flatten-on-end logic
- The architecture mirrors real quantitative systems while remaining compact and readable.

## Development Workflow
### This project follows an engineering workflow similar to production environments:
- Feature development on dedicated branches (e.g. feat/add-demo-config)
- Incremental commits with focused scope
- Merge into main via PR
- Tests required for new logic

## Roadmap (Planned)
 Unified CLI entrypoint
 Strategy registry & dynamic loading
 Vectorized backtest optimizations
 Paper trading (dry-run) mode
 Live trading adapters (broker-specific)
 Performance analytics & reporting

## Disclaimer
- This project is for research and educational purposes only.
- It is not investment advice and should not be used for real trading without proper validation, risk control, and compliance review.

# Author
## Andy-TJH
### Focus: Quantitative Systems/Backend Engineering/Test Development
### GitHub: https://github.com/Andy-TJH