"""find_best_windows: rank visibility windows by quality.

Pipeline:
  1. Resolve the target name.
  2. Compute visibility windows over the next N nights (visibility.windows).
  3. For each window, fetch the conditions forecast and score it on a 0..1 scale:
       0.5 * (1 - cloud_cover)       # optical clarity
     + 0.2 * peak_altitude_factor    # higher-up = lower air mass
     + 0.2 * seeing_factor           # 1.0 at 0.5\" → 0.2 at 3\"
     + 0.1 * window_duration_factor  # longer = better
  4. Sort descending; return up to ``limit`` results.

If conditions are unavailable (all providers down), windows are still returned with
a score representing visibility-only quality, so the system degrades gracefully
without ever silently producing fake data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from auto_telescope.catalog.targets import Target, resolve_target
from auto_telescope.conditions.aggregator import (
    AllProvidersDownError,
    ConditionsAggregator,
    ConditionsForecast,
)
from auto_telescope.config.settings import get_settings
from auto_telescope.config.site import MVHS_SITE, Site
from auto_telescope.visibility.windows import VisibilityWindow, compute_windows


@dataclass(frozen=True, slots=True)
class ScoredWindow:
    """A visibility window plus its quality score and supporting forecast."""

    target: Target
    window: VisibilityWindow
    score: float  # 0..1, higher is better
    forecast: ConditionsForecast | None
    score_breakdown: dict[str, float]


def find_best_windows(
    target_name: str,
    *,
    site: Site = MVHS_SITE,
    days: int = 7,
    limit: int = 10,
    min_altitude_deg: float | None = None,
    min_window_minutes: int | None = None,
    aggregator: ConditionsAggregator | None = None,
    now: datetime | None = None,
) -> list[ScoredWindow]:
    """Return the top-N best observation windows for ``target_name`` over the next ``days``.

    Args:
        target_name: Anything resolve_target accepts ("M42", "Jupiter", etc.).
        site:        Observing site (default: MVHS).
        days:        Number of nights to scan (default 7).
        limit:       Max number of windows to return (default 10).
        min_altitude_deg: Override settings.min_altitude_deg.
        min_window_minutes: Override settings.min_observation_minutes.
        aggregator:  Optional pre-built ConditionsAggregator (for tests).
        now:         Override "now" (UTC). For determinism in tests.
    """
    settings = get_settings()
    min_alt = min_altitude_deg if min_altitude_deg is not None else settings.min_altitude_deg
    min_dur = (
        min_window_minutes if min_window_minutes is not None else settings.min_observation_minutes
    )

    target = resolve_target(target_name, when_utc=now, site=site)

    start = (now or datetime.now(UTC)).astimezone(UTC)
    end = start + timedelta(days=days)

    windows = compute_windows(
        target.equatorial(),
        site=site,
        start_utc=start,
        end_utc=end,
        step_minutes=15,
        min_altitude_deg=min_alt,
        min_window_minutes=min_dur,
    )
    if not windows:
        return []

    forecasts: list[ConditionsForecast] = []
    if aggregator is None:
        aggregator = ConditionsAggregator()
    try:
        forecasts = aggregator.fetch(site.latitude, site.longitude)
    except AllProvidersDownError:
        forecasts = []

    scored: list[ScoredWindow] = []
    for w in windows:
        forecast = _forecast_for_window(forecasts, w)
        score, breakdown = _score(w, forecast)
        scored.append(
            ScoredWindow(
                target=target,
                window=w,
                score=score,
                forecast=forecast,
                score_breakdown=breakdown,
            )
        )

    scored.sort(key=lambda sw: sw.score, reverse=True)
    return scored[:limit]


def _forecast_for_window(
    forecasts: list[ConditionsForecast], window: VisibilityWindow
) -> ConditionsForecast | None:
    if not forecasts:
        return None
    # Find the forecast bucket nearest to the window's peak time.
    peak = window.peak_time_utc
    return min(forecasts, key=lambda f: abs((f.hour_utc - peak).total_seconds()))


def _score(
    window: VisibilityWindow, forecast: ConditionsForecast | None
) -> tuple[float, dict[str, float]]:
    breakdown: dict[str, float] = {}
    altitude_factor = max(0.0, min(1.0, (window.peak_altitude_deg - 20.0) / 60.0))
    breakdown["altitude"] = altitude_factor

    duration_factor = min(1.0, window.duration_minutes / 120.0)
    breakdown["duration"] = duration_factor

    if forecast is None:
        cloud_factor = 0.5  # unknown → middling
        seeing_factor = 0.5
    else:
        cloud_factor = max(0.0, 1.0 - forecast.cloud_cover_pct / 100.0)
        if forecast.seeing_arcsec is None:
            seeing_factor = 0.5
        else:
            # 0.5" → 1.0, 3" → ~0.2
            seeing_factor = max(0.0, min(1.0, 1.1 - (forecast.seeing_arcsec / 3.0)))

    breakdown["cloud"] = cloud_factor
    breakdown["seeing"] = seeing_factor

    score = (
        0.50 * cloud_factor + 0.20 * altitude_factor + 0.20 * seeing_factor + 0.10 * duration_factor
    )
    breakdown["total"] = score
    return score, breakdown
