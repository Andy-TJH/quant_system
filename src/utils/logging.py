from __future__ import annotations
import logging
import os
from datetime import datetime
from typing import Optional

_CONFIGURED = False

def setup_logging(
    run_id: Optional[str] = None,
    level: str = "INFO",
    log_dir: str = "logs",
) -> str:
    """
    Configure root logging once.
    - Console handler + File handler
    - File output: logs/app.<run_id>.log
    Returns the resolved run_id.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return run_id or "unknown"

    os.makedirs(log_dir, exist_ok=True)

    resolved_run_id = run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    file_path = os.path.join(log_dir, f"app.{resolved_run_id}.log")

    lvl = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(lvl)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console
    ch = logging.StreamHandler()
    ch.setLevel(lvl)
    ch.setFormatter(formatter)
    root.addHandler(ch)

    # File
    fh = logging.FileHandler(file_path, encoding="utf-8")
    fh.setLevel(lvl)
    fh.setFormatter(formatter)
    root.addHandler(fh)

    root.info("LOGGING_READY run_id=%s file=%s", resolved_run_id, file_path)
    _CONFIGURED = True
    return resolved_run_id

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
