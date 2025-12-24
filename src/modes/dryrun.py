from __future__ import annotations

from dataclasses import dataclass, field
from src.engine.event_loop import EventLoop
from src.utils.logging import get_logger

@dataclass
class DryRunConfig:
    """
    DryRun session behavior.
    - No forced flatten on end (paper trading can keep open positions)
    """
    emit_summary: bool = True

@dataclass
class DryRunMode:
    loop: EventLoop
    config: DryRunConfig = field(default_factory=DryRunConfig)

    def run(self) -> None:
        log = get_logger("mode.dryrun")
        log.info("DRYRUN_START")

        self.loop.run_until_data_end()

        if self.config.emit_summary:
            pos = getattr(self.loop.portfolio, "position", 0)
            log.info("DRYRUN_DONE final_position=%s", pos)
            print(f"DryRun done. Final position: {pos}")
        else:
            log.info("DRYRUN_DONE")
