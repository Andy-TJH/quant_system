from __future__ import annotations

import sys
from src.backtest.engine import main  

def main_entry() -> int:
    main()
    return 0

if __name__ == "__main__":
    raise SystemExit(main_entry())
