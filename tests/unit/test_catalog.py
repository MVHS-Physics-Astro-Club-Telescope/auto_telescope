"""Tests for catalog.curated, .targets, .feasibility, .solar_system."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from auto_telescope.catalog.curated import CURATED_TARGETS, get_curated_target
from auto_telescope.catalog.feasibility import assess_feasibility
from auto_telescope.catalog.solar_system import (
    SOLAR_SYSTEM_BODIES,
    is_solar_system_body,
    lookup_solar_system,
)
from auto_telescope.catalog.targets import Tier, resolve_target
from auto_telescope.config.site import MVHS_SITE


class TestCuratedCatalog:
    def test_catalog_size(self) -> None:
        assert len(CURATED_TARGETS) >= 50

    def test_unique_ids(self) -> None:
        ids = [t.id for t in CURATED_TARGETS]
        assert len(ids) == len(set(ids))

    def test_lookup_by_id(self) -> None:
        m13 = get_curated_target("M13")
        assert m13 is not None
        assert m13.id == "M13"

    def test_lookup_by_alias(self) -> None:
        m13 = get_curated_target("NGC 6205")
        assert m13 is not None
        assert m13.id == "M13"

    def test_lookup_case_insensitive(self) -> None:
        assert get_curated_target("m13") is get_curated_target("M13")

    def test_unknown_target(self) -> None:
        assert get_curated_target("nonexistent") is None

    def test_all_have_valid_coords(self) -> None:
        for t in CURATED_TARGETS:
            assert 0.0 <= t.ra_deg < 360.0
            assert -90.0 <= t.dec_deg <= 90.0

    def test_tier1_targets_have_descriptions(self) -> None:
        easy = [t for t in CURATED_TARGETS if t.tier == Tier.EASY]
        for t in easy:
            assert t.description != "", f"Tier 1 target {t.id} missing description"


class TestSolarSystem:
    def test_is_solar_system_body(self) -> None:
        assert is_solar_system_body("Jupiter")
        assert is_solar_system_body("jupiter")
        assert is_solar_system_body("the moon")
        assert not is_solar_system_body("M42")

    def test_lookup_jupiter_returns_real_coords(self) -> None:
        when = datetime(2026, 4, 1, 6, 0, tzinfo=UTC)
        jupiter = lookup_solar_system("Jupiter", when_utc=when, site=MVHS_SITE)
        assert jupiter.id == "jupiter"
        assert jupiter.display_name == "Jupiter"
        # Jupiter's RA/Dec aren't fixed; just sanity check ranges.
        assert 0.0 <= jupiter.ra_deg < 360.0
        assert -30.0 <= jupiter.dec_deg <= 30.0  # Jupiter stays near the ecliptic

    def test_solar_system_count(self) -> None:
        assert len(SOLAR_SYSTEM_BODIES) >= 8  # Sun, Moon, 7 planets at minimum (we exclude Pluto)

    def test_unknown_body_raises(self) -> None:
        with pytest.raises(KeyError):
            lookup_solar_system("Pluto")


class TestResolveTarget:
    def test_resolves_curated(self) -> None:
        t = resolve_target("M42_core")
        assert t.id == "M42_core"

    def test_resolves_solar_system(self) -> None:
        t = resolve_target("Jupiter")
        assert t.id == "jupiter"

    def test_unknown_raises_keyerror(self) -> None:
        # Use a name SIMBAD won't resolve either; "nonexistent_xyz_123" is safe.
        with pytest.raises(KeyError):
            resolve_target("definitelynotastar_xyz_zz")


class TestFeasibility:
    def test_tier1_target_is_feasible(self) -> None:
        m13 = get_curated_target("M13")
        assert m13 is not None
        verdict = assess_feasibility(m13, site=MVHS_SITE)
        assert verdict.feasible

    def test_tier3_target_rejected(self) -> None:
        horsehead = get_curated_target("Horsehead")
        assert horsehead is not None
        verdict = assess_feasibility(horsehead, site=MVHS_SITE)
        assert not verdict.feasible

    def test_southern_target_rejected(self) -> None:
        m4 = get_curated_target("M4")
        assert m4 is not None
        # M4 at dec -26.5 from lat +37: max alt = 90 - |37 - (-26.5)| = 26.5 deg.
        # That's above the default 20 deg horizon → feasible.
        verdict = assess_feasibility(m4, site=MVHS_SITE, safety_horizon_deg=20.0)
        assert verdict.feasible
        # But strict horizon → not feasible.
        verdict_strict = assess_feasibility(m4, site=MVHS_SITE, safety_horizon_deg=30.0)
        assert not verdict_strict.feasible

    def test_faint_target_rejected_by_magnitude_limit(self) -> None:
        m13 = get_curated_target("M13")
        assert m13 is not None
        verdict = assess_feasibility(m13, site=MVHS_SITE, magnitude_limit=4.0)
        assert not verdict.feasible
        assert "mag" in verdict.reason
