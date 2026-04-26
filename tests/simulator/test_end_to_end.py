"""End-to-end simulator tests: drive the scheduler with mocked providers.

These prove the full pipeline (catalog → visibility → conditions → scheduler) works
without depending on external APIs. The conditions aggregator is replaced with a
stub that returns deterministic forecasts.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from auto_telescope.conditions.aggregator import ConditionsAggregator, ConditionsForecast
from auto_telescope.config.site import MVHS_SITE
from auto_telescope.scheduler.best_time import find_best_windows


def _stub_forecasts(start: datetime, hours: int = 168) -> list[ConditionsForecast]:
    forecasts = []
    for i in range(hours):
        forecasts.append(
            ConditionsForecast(
                hour_utc=start.replace(minute=0, second=0, microsecond=0) + timedelta(hours=i),
                cloud_cover_pct=10.0 + (i % 12) * 5,  # varies 10..65
                wind_speed_mps=2.0,
                seeing_arcsec=1.5,
                transparency_mag=0.4,
                visibility_m=20000.0,
                temperature_c=18.0,
                relative_humidity_pct=40.0,
                contributing_providers=("7timer", "nws", "open-meteo"),
            )
        )
    return forecasts


def test_find_best_windows_for_polaris_returns_results() -> None:
    """Polaris is circumpolar; we should always get at least 1 window per night."""
    now = datetime(2026, 7, 4, 0, tzinfo=UTC)
    stub = _stub_forecasts(now, hours=24 * 8)

    with patch.object(ConditionsAggregator, "fetch", return_value=stub):
        windows = find_best_windows(
            "Polaris",
            site=MVHS_SITE,
            days=7,
            limit=10,
            now=now,
        )
    assert len(windows) > 0
    for w in windows:
        assert 0.0 <= w.score <= 1.0
        assert w.target.id == "Polaris"
        # Window must be inside the 7-day horizon.
        assert w.window.start_utc >= now
        assert w.window.start_utc <= now + timedelta(days=8)


def test_find_best_windows_for_jupiter() -> None:
    now = datetime(2026, 7, 4, 0, tzinfo=UTC)
    stub = _stub_forecasts(now, hours=24 * 8)
    with patch.object(ConditionsAggregator, "fetch", return_value=stub):
        windows = find_best_windows("Jupiter", site=MVHS_SITE, days=7, now=now)
    assert all(w.target.id == "jupiter" for w in windows)


def test_find_best_windows_returns_sorted_by_score() -> None:
    now = datetime(2026, 7, 4, 0, tzinfo=UTC)
    stub = _stub_forecasts(now, hours=24 * 8)
    with patch.object(ConditionsAggregator, "fetch", return_value=stub):
        windows = find_best_windows("M13", site=MVHS_SITE, days=7, now=now)
    if len(windows) > 1:
        scores = [w.score for w in windows]
        assert scores == sorted(scores, reverse=True)


def test_find_best_windows_unknown_target_raises() -> None:
    with pytest.raises(KeyError):
        find_best_windows("definitelynotastar_xyz_zz", days=1)


def test_find_best_windows_handles_no_forecasts() -> None:
    """If conditions are unavailable we still return visibility-only windows."""
    now = datetime(2026, 7, 4, 0, tzinfo=UTC)
    from auto_telescope.conditions.aggregator import AllProvidersDownError

    with patch.object(ConditionsAggregator, "fetch", side_effect=AllProvidersDownError("test")):
        windows = find_best_windows("Polaris", site=MVHS_SITE, days=2, now=now)
    assert len(windows) > 0
    for w in windows:
        # No forecast → score breakdown shows the cloud factor as the fallback 0.5.
        assert w.forecast is None
        assert w.score_breakdown["cloud"] == 0.5
