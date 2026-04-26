"""Scheduler: pick the best windows over the next N nights for a given target."""

from auto_telescope.scheduler.best_time import (
    ScoredWindow,
    find_best_windows,
)

__all__ = ["ScoredWindow", "find_best_windows"]
