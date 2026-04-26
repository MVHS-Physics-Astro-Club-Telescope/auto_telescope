"""NOAA / National Weather Service forecast provider (api.weather.gov).

Two-step API:
  1. GET /points/{lat},{lon}  →  returns the hourly forecast URL for that gridpoint.
  2. GET <forecastHourly URL> →  returns hourly periods (1-hour resolution, 156 hours).

The User-Agent is mandatory; NWS will 403 without one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
from dateutil import parser as date_parser

NWS_POINTS_URL = "https://api.weather.gov/points/{lat:.4f},{lon:.4f}"


@dataclass(frozen=True, slots=True)
class NWSSlot:
    """One hourly forecast period from NWS."""

    start_utc: datetime
    end_utc: datetime
    temperature_c: float
    wind_speed_mps: float
    wind_direction_deg: float | None
    short_forecast: str
    cloud_cover_pct: float | None
    precipitation_probability_pct: float | None


class NWSProvider:
    """Adapter for the api.weather.gov hourly forecast."""

    name = "nws"

    def __init__(
        self, *, timeout_seconds: float = 10.0, user_agent: str = "auto-telescope/0.1"
    ) -> None:
        self._timeout = timeout_seconds
        # NWS REQUIRES a real User-Agent including contact info.
        self._headers = {
            "User-Agent": user_agent,
            "Accept": "application/geo+json",
        }

    def fetch(self, latitude: float, longitude: float) -> list[NWSSlot]:
        """Fetch hourly forecast for a site. Two HTTP calls: /points then forecastHourly."""
        points_url = NWS_POINTS_URL.format(lat=latitude, lon=longitude)
        points_resp = requests.get(points_url, timeout=self._timeout, headers=self._headers)
        points_resp.raise_for_status()
        points = points_resp.json()
        forecast_url = points["properties"]["forecastHourly"]

        hourly_resp = requests.get(forecast_url, timeout=self._timeout, headers=self._headers)
        hourly_resp.raise_for_status()
        return self._parse(hourly_resp.json())

    def _parse(self, payload: dict[str, Any]) -> list[NWSSlot]:
        periods = payload.get("properties", {}).get("periods", [])
        if not periods:
            raise ValueError(f"NWS hourly payload missing periods: {payload!r}")

        slots: list[NWSSlot] = []
        for p in periods:
            start = date_parser.isoparse(p["startTime"])
            end = date_parser.isoparse(p["endTime"])

            temp_unit = (p.get("temperatureUnit") or "F").upper()
            temp_val = float(p.get("temperature", 0))
            temp_c = temp_val if temp_unit == "C" else (temp_val - 32) * 5.0 / 9.0

            wind_speed_mps = _parse_wind_speed(p.get("windSpeed", "0 mph"))
            wind_dir = _parse_wind_direction(p.get("windDirection"))

            cloud_pct = _maybe_qv(p, "cloudCover", "skyCover")  # NWS uses skyCover in %
            precip_pct = _maybe_qv(p, "probabilityOfPrecipitation")

            slots.append(
                NWSSlot(
                    start_utc=start.astimezone(start.tzinfo) if start.tzinfo else start,
                    end_utc=end.astimezone(end.tzinfo) if end.tzinfo else end,
                    temperature_c=temp_c,
                    wind_speed_mps=wind_speed_mps,
                    wind_direction_deg=wind_dir,
                    short_forecast=p.get("shortForecast", ""),
                    cloud_cover_pct=cloud_pct,
                    precipitation_probability_pct=precip_pct,
                )
            )
        return slots


def _parse_wind_speed(raw: str | dict[str, Any]) -> float:
    """NWS may return '5 mph', '5 to 10 mph', or a quantitative-value dict."""
    if isinstance(raw, dict):
        # Quantitative value: {"unitCode": "wmoUnit:km_h-1", "value": 8.0}
        unit = raw.get("unitCode") or ""
        v = raw.get("value")
        if v is None:
            return 0.0
        if "km_h-1" in unit or "km/h" in unit:
            return float(v) * 1000.0 / 3600.0
        if "mph" in unit or "mi_h-1" in unit:
            return float(v) * 0.44704
        return float(v)  # assume m/s
    s = str(raw).strip().lower()
    # Take the upper bound of any "X to Y" range — be conservative on wind.
    parts = s.replace("to", " ").split()
    nums = [float(t) for t in parts if t.replace(".", "", 1).isdigit()]
    mph = max(nums) if nums else 0.0
    return mph * 0.44704


def _parse_wind_direction(raw: str | None) -> float | None:
    if not raw:
        return None
    compass = {
        "N": 0,
        "NNE": 22.5,
        "NE": 45,
        "ENE": 67.5,
        "E": 90,
        "ESE": 112.5,
        "SE": 135,
        "SSE": 157.5,
        "S": 180,
        "SSW": 202.5,
        "SW": 225,
        "WSW": 247.5,
        "W": 270,
        "WNW": 292.5,
        "NW": 315,
        "NNW": 337.5,
    }
    return compass.get(str(raw).upper())


def _maybe_qv(period: dict[str, Any], *keys: str) -> float | None:
    """Pull a numeric value out of a quantitative-value field if present."""
    for k in keys:
        v = period.get(k)
        if v is None:
            continue
        if isinstance(v, dict):
            value = v.get("value")
            if value is not None:
                return float(value)
        else:
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return None
