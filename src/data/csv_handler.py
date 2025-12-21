from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Iterable

from src.core.events import EventType, MarketEvent


def _parse_datetime_to_ms(s: str) -> int:
    s = s.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(s, fmt)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue

    try:
        x = float(s)
        if x > 1e12:
            return int(x)
        return int(x * 1000)
    except ValueError as e:
        raise ValueError(f"Unrecognized datetime format: {s}") from e
    

@dataclass
class CSVHandler:
    csv_path: str
    symbol: str

    col_datetime: str = "datetime"
    col_open: str = "open"
    col_high: str = "high"
    col_low: str = "low"
    col_close: str = "close"
    col_volume: str = "volume"

    def __post_init__(self) -> None:
        path = Path(self.csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        self._rows: List[dict] = []
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError("CSV file has no header row.")
            self._rows = list(reader)

        if not self._rows:
            raise ValueError("CSV is empty.")
        
        self._i = 0
        self._latest_bars: Dict[str, List[MarketEvent]] = {self.symbol: []}

    
    def has_next(self) -> bool:
        return self._i < len(self._rows)
    
    def stream_next(self) -> MarketEvent:
        row = self._rows[self._i]
        self._i += 1

        ts_ms = _parse_datetime_to_ms(row[self.col_datetime])
        o = float(row[self.col_open])
        h = float(row[self.col_high])
        l = float(row[self.col_low])
        c = float(row[self.col_close])
        v = float(row.get(self.col_volume, 0.0) or 0.0)

        event = MarketEvent(
            type = EventType.MARKET,
            timestamp_ms = ts_ms,
            symbol = self.symbol,
            open = o, high = h, low = l, close = c, volume = v
        )
        self._latest_bars[self.symbol].append(event)
        return event
    
    def get_latest_bars(self, symbol: str, n: int = 1) -> List[MarketEvent]:
        bars = self._latest_bars.get(symbol, [])
        if n <= 0:
            return []
        return bars[-n:]
    
    def get_latest_close(self, symbol: str) -> Optional[float]:
        bars = self._latest_bars.get(symbol, [])
        return bars[-1].close if bars else None
    