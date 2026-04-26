"""Unit tests for provider parsers — pure logic, no network."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from auto_telescope.conditions.aggregator import (
    AllProvidersDownError,
    ConditionsAggregator,
)
from auto_telescope.conditions.nws import NWSProvider, _parse_wind_direction, _parse_wind_speed
from auto_telescope.conditions.open_meteo import OpenMeteoProvider
from auto_telescope.conditions.seven_timer import SevenTimerProvider


class TestSevenTimerParsing:
    def test_parses_minimal_payload(self) -> None:
        provider = SevenTimerProvider()
        payload = {
            "init": "2026040100",
            "dataseries": [
                {
                    "timepoint": 3,
                    "cloudcover": 1,
                    "seeing": 2,
                    "transparency": 3,
                    "wind10m": {"speed": 2},
                    "rh2m": "1",
                    "temp2m": 12,
                },
                {
                    "timepoint": 6,
                    "cloudcover": 9,
                    "seeing": 8,
                    "transparency": 8,
                    "wind10m": {"speed": 5},
                    "rh2m": "3",
                    "temp2m": 15,
                },
            ],
        }
        slots = provider._parse(payload)
        assert len(slots) == 2
        s0, s1 = slots
        assert s0.timestamp_utc == datetime(2026, 4, 1, 3, tzinfo=UTC)
        assert s0.cloud_cover_pct < 10  # index 1 = ~3%
        assert s1.cloud_cover_pct > 90  # index 9 = ~97%
        assert s0.seeing_arcsec < s1.seeing_arcsec

    def test_missing_dataseries_raises(self) -> None:
        provider = SevenTimerProvider()
        with pytest.raises(ValueError):
            provider._parse({"init": "2026040100"})


class TestNWSParsing:
    def test_parses_periods(self) -> None:
        provider = NWSProvider()
        payload = {
            "properties": {
                "periods": [
                    {
                        "startTime": "2026-04-01T00:00:00-07:00",
                        "endTime": "2026-04-01T01:00:00-07:00",
                        "temperature": 50,
                        "temperatureUnit": "F",
                        "windSpeed": "5 mph",
                        "windDirection": "NW",
                        "shortForecast": "Clear",
                        "skyCover": 5,
                        "probabilityOfPrecipitation": {"unitCode": "wmoUnit:percent", "value": 10},
                    },
                ]
            }
        }
        slots = provider._parse(payload)
        assert len(slots) == 1
        s = slots[0]
        assert s.temperature_c == pytest.approx(10.0, abs=0.1)  # 50F = 10C
        assert s.wind_speed_mps == pytest.approx(2.2352, abs=0.01)
        assert s.wind_direction_deg == 315.0
        assert s.cloud_cover_pct == 5.0
        assert s.precipitation_probability_pct == 10.0

    def test_parse_wind_speed_range(self) -> None:
        # NWS sometimes gives "5 to 10 mph" — we conservatively pick the high end.
        assert _parse_wind_speed("5 to 10 mph") == pytest.approx(10 * 0.44704, abs=1e-3)

    def test_parse_wind_speed_qv_kmh(self) -> None:
        v = _parse_wind_speed({"unitCode": "wmoUnit:km_h-1", "value": 18.0})
        assert v == pytest.approx(5.0, abs=0.01)

    def test_parse_wind_direction(self) -> None:
        assert _parse_wind_direction("NE") == 45.0
        assert _parse_wind_direction(None) is None

    def test_missing_periods_raises(self) -> None:
        with pytest.raises(ValueError):
            NWSProvider()._parse({"properties": {}})


class TestOpenMeteoParsing:
    def test_parses_hourly(self) -> None:
        provider = OpenMeteoProvider()
        payload = {
            "hourly": {
                "time": ["2026-04-01T00:00", "2026-04-01T01:00"],
                "cloud_cover": [50, 60],
                "visibility": [10000, 8000],
                "wind_speed_10m": [3.0, 5.0],
            }
        }
        slots = provider._parse(payload)
        assert len(slots) == 2
        assert slots[0].cloud_cover_pct == 50.0
        assert slots[1].wind_speed_mps == 5.0


class TestAggregator:
    def test_all_providers_down_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        agg = ConditionsAggregator()

        def boom(self, lat: float, lon: float) -> list:
            raise RuntimeError("simulated outage")

        monkeypatch.setattr(SevenTimerProvider, "fetch", boom, raising=True)
        monkeypatch.setattr(NWSProvider, "fetch", boom, raising=True)
        monkeypatch.setattr(OpenMeteoProvider, "fetch", boom, raising=True)

        with pytest.raises(AllProvidersDownError):
            agg.fetch(37.366, -122.077)

    def test_partial_outage_still_returns_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from auto_telescope.conditions.seven_timer import SevenTimerSlot

        agg = ConditionsAggregator()

        def good(self, lat: float, lon: float) -> list:
            return [
                SevenTimerSlot(
                    timestamp_utc=datetime(2026, 4, 1, 3, tzinfo=UTC),
                    cloud_cover_pct=20.0,
                    seeing_arcsec=1.0,
                    transparency_mag=0.5,
                    wind10m_mps=2.0,
                    relative_humidity_pct=40.0,
                    temperature_c=15.0,
                ),
            ]

        def boom(self, lat: float, lon: float) -> list:
            raise RuntimeError("simulated outage")

        monkeypatch.setattr(SevenTimerProvider, "fetch", good, raising=True)
        monkeypatch.setattr(NWSProvider, "fetch", boom, raising=True)
        monkeypatch.setattr(OpenMeteoProvider, "fetch", boom, raising=True)

        forecasts = agg.fetch(37.366, -122.077)
        assert len(forecasts) == 3  # 7Timer expanded across 3 hours
        for f in forecasts:
            assert f.contributing_providers == ("7timer",)
            assert f.cloud_cover_pct == 20.0
