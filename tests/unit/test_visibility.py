"""Tests for visibility.horizons, .rules, .windows."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from auto_telescope.config.site import MVHS_SITE
from auto_telescope.visibility.coordinates import EquatorialCoord
from auto_telescope.visibility.horizons import (
    is_above_horizon,
    sun_altitude,
    sun_below_horizon,
)
from auto_telescope.visibility.rules import is_visible
from auto_telescope.visibility.windows import compute_windows

# Polaris — circumpolar from +37 deg latitude.
POLARIS = EquatorialCoord(ra_deg=37.95, dec_deg=89.26)
# A southern target that is BELOW the horizon from MVHS most of the day.
DEEP_SOUTH = EquatorialCoord(ra_deg=100.0, dec_deg=-70.0)


class TestSunAltitude:
    def test_sun_below_at_local_midnight(self) -> None:
        # 4 July 2026 at 8 UTC = 1 AM PDT in Mountain View.
        when = datetime(2026, 7, 4, 8, 0, tzinfo=UTC)
        assert sun_below_horizon(when, MVHS_SITE, twilight_deg=18.0)

    def test_sun_above_at_local_noon(self) -> None:
        # 4 July 2026 at 20 UTC = 1 PM PDT.
        when = datetime(2026, 7, 4, 20, 0, tzinfo=UTC)
        assert sun_altitude(when, MVHS_SITE).altitude_deg > 60.0


class TestHorizon:
    def test_polaris_always_above(self) -> None:
        when = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        assert is_above_horizon(POLARIS, when, MVHS_SITE, min_altitude_deg=20.0)

    def test_deep_south_never_above(self) -> None:
        # Sample 24 hours and assert it never reaches 20 deg.
        base = datetime(2026, 4, 1, tzinfo=UTC)
        for hour in range(24):
            assert not is_above_horizon(
                DEEP_SOUTH, base + timedelta(hours=hour), MVHS_SITE, min_altitude_deg=20.0
            )


class TestVisibilityRule:
    def test_polaris_visible_at_local_midnight(self) -> None:
        when = datetime(2026, 1, 15, 8, 0, tzinfo=UTC)  # 12 AM PST
        verdict = is_visible(
            POLARIS,
            when,
            MVHS_SITE,
            min_altitude_deg=20.0,
            require_sun_below_deg=6.0,
            min_moon_separation_deg=0.0,
        )
        assert verdict.visible, verdict.reason

    def test_target_invisible_during_day(self) -> None:
        when = datetime(2026, 7, 4, 20, 0, tzinfo=UTC)  # 1 PM PDT
        verdict = is_visible(POLARIS, when, MVHS_SITE)
        assert not verdict.visible
        assert "sun" in verdict.reason.lower()


class TestComputeWindows:
    def test_polaris_yields_long_windows(self) -> None:
        start = datetime(2026, 1, 15, 0, 0, tzinfo=UTC)
        end = start + timedelta(days=1)
        windows = compute_windows(
            POLARIS,
            site=MVHS_SITE,
            start_utc=start,
            end_utc=end,
            step_minutes=30,
            min_altitude_deg=20.0,
            min_window_minutes=30,
        )
        assert len(windows) >= 1
        total = sum(w.duration_minutes for w in windows)
        # Polaris is always above 20 deg from MVHS, but only "visible" when sun is down.
        # That should give at least 8 hours of window in a January night.
        assert total >= 8 * 60

    def test_deep_south_yields_no_windows(self) -> None:
        start = datetime(2026, 4, 1, tzinfo=UTC)
        end = start + timedelta(days=1)
        windows = compute_windows(
            DEEP_SOUTH,
            site=MVHS_SITE,
            start_utc=start,
            end_utc=end,
            step_minutes=30,
            min_altitude_deg=20.0,
            min_window_minutes=30,
        )
        assert windows == []

    def test_zero_duration_input(self) -> None:
        when = datetime(2026, 1, 1, tzinfo=UTC)
        windows = compute_windows(
            POLARIS,
            site=MVHS_SITE,
            start_utc=when,
            end_utc=when,
        )
        assert windows == []
