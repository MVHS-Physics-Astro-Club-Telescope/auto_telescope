"""7Timer! ASTRO forecast provider.

API docs: https://www.7timer.info/doc.php?lang=en

Why we trust this for astronomy: it's the only one of our three providers that
publishes seeing (atmospheric turbulence) and transparency (sky clarity)
forecasts on a 0-8 / 1-8 scale specifically tuned for amateur observers.

Returns hourly forecasts in 3-hour resolution out to ~96 hours.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import requests

SEVEN_TIMER_URL = "https://www.7timer.info/bin/api.pl"


@dataclass(frozen=True, slots=True)
class SevenTimerSlot:
    """One 3-hour forecast slot from 7Timer! ASTRO."""

    timestamp_utc: datetime
    cloud_cover_pct: float  # 0-100. 7Timer returns 1-9, we normalize.
    seeing_arcsec: float  # 0.5-3.0+. 7Timer returns 1-8, we map to arcsec.
    transparency_mag: float  # 0.3-1.0 approx. 1=excellent, 8=poor.
    wind10m_mps: float  # m/s
    relative_humidity_pct: float  # 0-100
    temperature_c: float  # Celsius


# 7Timer cloud cover index → percentage midpoint
# (1=0-6%, 2=6-19%, 3=19-31%, 4=31-44%, 5=44-56%, 6=56-69%, 7=69-81%, 8=81-94%, 9=94-100%)
_CLOUD_PCT = {1: 3, 2: 12, 3: 25, 4: 38, 5: 50, 6: 62, 7: 75, 8: 88, 9: 97}

# 7Timer seeing index → arcsec (1=<0.5, 2=0.5-0.75, 3=0.75-1, 4=1-1.25, 5=1.25-1.5,
# 6=1.5-2, 7=2-2.5, 8=>2.5)
_SEEING_ARCSEC = {1: 0.4, 2: 0.6, 3: 0.85, 4: 1.1, 5: 1.4, 6: 1.75, 7: 2.25, 8: 3.0}

# 7Timer transparency index → mag/airmass extinction (1=<0.3, 2=0.3-0.4, ... 8=>1.0)
_TRANSPARENCY_MAG = {1: 0.25, 2: 0.35, 3: 0.45, 4: 0.55, 5: 0.65, 6: 0.75, 7: 0.85, 8: 1.05}

# 7Timer wind10m index (1-8) → m/s midpoint
_WIND_MPS = {1: 0.3, 2: 1.5, 3: 3.5, 4: 6.0, 5: 9.0, 6: 12.5, 7: 16.5, 8: 21.0}

# 7Timer rh2m string ("-4" through "4") → percent
_RH_PCT = {
    "-4": 5,
    "-3": 12,
    "-2": 20,
    "-1": 30,
    "0": 45,
    "1": 60,
    "2": 72,
    "3": 82,
    "4": 92,
}


class SevenTimerProvider:
    """Adapter for the 7Timer! ASTRO endpoint."""

    name = "7timer"

    def __init__(
        self, *, timeout_seconds: float = 10.0, user_agent: str = "auto-telescope/0.1"
    ) -> None:
        self._timeout = timeout_seconds
        self._headers = {"User-Agent": user_agent}

    def fetch(self, latitude: float, longitude: float) -> list[SevenTimerSlot]:
        """Fetch the ASTRO forecast for a site. Returns up to ~32 slots (96h / 3h)."""
        params = {
            "lon": f"{longitude:.4f}",
            "lat": f"{latitude:.4f}",
            "product": "astro",
            "output": "json",
        }
        response = requests.get(
            SEVEN_TIMER_URL,
            params=params,
            timeout=self._timeout,
            headers=self._headers,
        )
        response.raise_for_status()
        return self._parse(response.json())

    def _parse(self, payload: dict[str, Any]) -> list[SevenTimerSlot]:
        init_str = payload.get("init")
        series = payload.get("dataseries") or []
        if not init_str or not series:
            raise ValueError(f"7Timer payload missing init/dataseries: {payload!r}")
        # init format YYYYMMDDHH (UTC)
        init = datetime.strptime(init_str, "%Y%m%d%H").replace(tzinfo=UTC)

        slots: list[SevenTimerSlot] = []
        for entry in series:
            ts = init + timedelta(hours=int(entry["timepoint"]))
            cloud = int(entry.get("cloudcover", 9))
            seeing = int(entry.get("seeing", 8))
            transp = int(entry.get("transparency", 8))
            wind = (
                int(entry.get("wind10m", {}).get("speed", 4))
                if isinstance(entry.get("wind10m"), dict)
                else int(entry.get("wind10m", 4))
            )
            rh_raw = str(entry.get("rh2m", "0"))
            temp = float(entry.get("temp2m", 0))

            slots.append(
                SevenTimerSlot(
                    timestamp_utc=ts,
                    cloud_cover_pct=float(_CLOUD_PCT.get(cloud, 100)),
                    seeing_arcsec=float(_SEEING_ARCSEC.get(seeing, 3.0)),
                    transparency_mag=float(_TRANSPARENCY_MAG.get(transp, 1.05)),
                    wind10m_mps=float(_WIND_MPS.get(wind, 21.0)),
                    relative_humidity_pct=float(_RH_PCT.get(rh_raw, 50)),
                    temperature_c=temp,
                )
            )
        return slots
