"""Open-Meteo forecast provider.

API: https://open-meteo.com/en/docs

Open-Meteo is our backup. It's free, requires no API key, and has good
worldwide coverage. We pull cloud_cover, visibility, and wind_speed_10m
on hourly resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
from dateutil import parser as date_parser

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True, slots=True)
class OpenMeteoSlot:
    """One hourly forecast slot from Open-Meteo."""

    timestamp_utc: datetime
    cloud_cover_pct: float
    visibility_m: float
    wind_speed_mps: float


class OpenMeteoProvider:
    """Adapter for the Open-Meteo hourly endpoint."""

    name = "open-meteo"

    def __init__(
        self, *, timeout_seconds: float = 10.0, user_agent: str = "auto-telescope/0.1"
    ) -> None:
        self._timeout = timeout_seconds
        self._headers = {"User-Agent": user_agent}

    def fetch(self, latitude: float, longitude: float) -> list[OpenMeteoSlot]:
        params = {
            "latitude": f"{latitude:.4f}",
            "longitude": f"{longitude:.4f}",
            "hourly": "cloud_cover,visibility,wind_speed_10m",
            "wind_speed_unit": "ms",
            "timezone": "UTC",
        }
        resp = requests.get(
            OPEN_METEO_URL, params=params, timeout=self._timeout, headers=self._headers
        )
        resp.raise_for_status()
        return self._parse(resp.json())

    def _parse(self, payload: dict[str, Any]) -> list[OpenMeteoSlot]:
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        clouds = hourly.get("cloud_cover") or []
        visibilities = hourly.get("visibility") or []
        winds = hourly.get("wind_speed_10m") or []

        if not times:
            raise ValueError(f"Open-Meteo payload missing hourly.time: {payload!r}")

        n = min(len(times), len(clouds), len(visibilities), len(winds))
        slots: list[OpenMeteoSlot] = []
        for i in range(n):
            ts = date_parser.isoparse(times[i])
            slots.append(
                OpenMeteoSlot(
                    timestamp_utc=ts,
                    cloud_cover_pct=float(clouds[i]) if clouds[i] is not None else 100.0,
                    visibility_m=float(visibilities[i]) if visibilities[i] is not None else 0.0,
                    wind_speed_mps=float(winds[i]) if winds[i] is not None else 0.0,
                )
            )
        return slots
