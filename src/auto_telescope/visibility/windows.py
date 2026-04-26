"""Compute observation windows: contiguous runs of time when a target is visible.

Walks a time grid (default 5-min steps) over a date range, calls ``is_visible`` at
each step, and returns the contiguous "visible" segments at least
``min_window_minutes`` long.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from auto_telescope.config.site import Site
from auto_telescope.visibility.coordinates import EquatorialCoord
from auto_telescope.visibility.rules import is_visible


@dataclass(frozen=True, slots=True)
class VisibilityWindow:
    """A contiguous block of time during which the target is visible."""

    start_utc: datetime
    end_utc: datetime
    peak_altitude_deg: float
    peak_time_utc: datetime

    @property
    def duration_minutes(self) -> float:
        return (self.end_utc - self.start_utc).total_seconds() / 60.0


def compute_windows(
    coord: EquatorialCoord,
    *,
    site: Site,
    start_utc: datetime,
    end_utc: datetime,
    step_minutes: int = 5,
    min_altitude_deg: float = 20.0,
    require_sun_below_deg: float = 6.0,
    min_window_minutes: int = 30,
) -> list[VisibilityWindow]:
    """Walk the time grid and return all visibility windows >= min_window_minutes."""
    if start_utc.tzinfo is None:
        start_utc = start_utc.replace(tzinfo=UTC)
    if end_utc.tzinfo is None:
        end_utc = end_utc.replace(tzinfo=UTC)
    if end_utc <= start_utc:
        return []

    step = timedelta(minutes=step_minutes)
    windows: list[VisibilityWindow] = []

    current_start: datetime | None = None
    peak_alt = -90.0
    peak_time: datetime | None = None

    t = start_utc
    while t <= end_utc:
        verdict = is_visible(
            coord,
            t,
            site,
            min_altitude_deg=min_altitude_deg,
            require_sun_below_deg=require_sun_below_deg,
        )
        if verdict.visible:
            if current_start is None:
                current_start = t
                peak_alt = verdict.altitude_deg
                peak_time = t
            elif verdict.altitude_deg > peak_alt:
                peak_alt = verdict.altitude_deg
                peak_time = t
        else:
            if current_start is not None and peak_time is not None:
                window_end = t
                duration_min = (window_end - current_start).total_seconds() / 60.0
                if duration_min >= min_window_minutes:
                    windows.append(
                        VisibilityWindow(
                            start_utc=current_start,
                            end_utc=window_end,
                            peak_altitude_deg=peak_alt,
                            peak_time_utc=peak_time,
                        )
                    )
                current_start = None
                peak_alt = -90.0
                peak_time = None
        t += step

    # Close any open window at the end.
    if current_start is not None and peak_time is not None:
        duration_min = (end_utc - current_start).total_seconds() / 60.0
        if duration_min >= min_window_minutes:
            windows.append(
                VisibilityWindow(
                    start_utc=current_start,
                    end_utc=end_utc,
                    peak_altitude_deg=peak_alt,
                    peak_time_utc=peak_time,
                )
            )

    return windows
