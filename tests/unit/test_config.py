"""Tests for config.site and config.settings."""

from __future__ import annotations

import pytest

from auto_telescope.config.settings import Settings
from auto_telescope.config.site import MVHS_SITE, Site


class TestSite:
    def test_mvhs_site_defaults(self) -> None:
        assert MVHS_SITE.name == "Mountain View High School"
        assert abs(MVHS_SITE.latitude - 37.366) < 1e-6
        assert abs(MVHS_SITE.longitude - (-122.077)) < 1e-6
        assert MVHS_SITE.timezone == "America/Los_Angeles"

    def test_to_earth_location_round_trips(self) -> None:
        loc = MVHS_SITE.to_earth_location()
        assert loc.lat.degree == pytest.approx(MVHS_SITE.latitude, abs=1e-6)
        assert loc.lon.degree == pytest.approx(MVHS_SITE.longitude, abs=1e-6)

    @pytest.mark.parametrize("bad_lat", [-91.0, 91.0, 100.0])
    def test_invalid_latitude(self, bad_lat: float) -> None:
        with pytest.raises(ValueError):
            Site(name="x", latitude=bad_lat, longitude=0.0, elevation_m=0.0)

    @pytest.mark.parametrize("bad_lon", [-181.0, 181.0])
    def test_invalid_longitude(self, bad_lon: float) -> None:
        with pytest.raises(ValueError):
            Site(name="x", latitude=0.0, longitude=bad_lon, elevation_m=0.0)

    @pytest.mark.parametrize("bad_elev", [-1000.0, 10000.0])
    def test_invalid_elevation(self, bad_elev: float) -> None:
        with pytest.raises(ValueError):
            Site(name="x", latitude=0.0, longitude=0.0, elevation_m=bad_elev)


class TestSettings:
    def test_defaults_match_mvhs(self) -> None:
        s = Settings()
        site = s.to_site()
        assert site.latitude == MVHS_SITE.latitude
        assert site.longitude == MVHS_SITE.longitude

    def test_env_var_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AUTO_TELESCOPE_LATITUDE", "0.0")
        monkeypatch.setenv("AUTO_TELESCOPE_LONGITUDE", "0.0")
        s = Settings()
        assert s.latitude == 0.0
        assert s.longitude == 0.0
