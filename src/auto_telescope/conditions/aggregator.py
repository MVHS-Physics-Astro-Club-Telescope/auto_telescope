"""Aggregator that reconciles three providers into a single forecast.

Strategy:
  * Bucket every provider's slots into clock hours (UTC).
  * For each hour, compute conservative consensus values:
      cloud_cover = max(provider_clouds)              # most pessimistic
      wind_speed  = max(provider_winds)
      seeing      = 7Timer's value (only one that publishes seeing)
      transp      = 7Timer's value
  * If 7Timer is down we still get cloud + wind. If two of the three are down,
    we still produce a forecast. If all three are down, raise AllProvidersDownError.

The aggregator never silently degrades: every produced ForecastSlot records
which providers contributed, so the safety layer can decide whether to slew.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from auto_telescope.conditions.cache import ConditionsCache
from auto_telescope.conditions.nws import NWSProvider, NWSSlot
from auto_telescope.conditions.open_meteo import OpenMeteoProvider, OpenMeteoSlot
from auto_telescope.conditions.seven_timer import SevenTimerProvider, SevenTimerSlot

log = logging.getLogger(__name__)


class AllProvidersDownError(RuntimeError):
    """Raised when every provider failed; safety layer must NOT slew on this."""


@dataclass(frozen=True, slots=True)
class ConditionsForecast:
    """Aggregated conditions for a single hour, plus provenance."""

    hour_utc: datetime  # top of the hour, UTC
    cloud_cover_pct: float  # 0-100, max across providers
    wind_speed_mps: float  # max across providers
    seeing_arcsec: float | None  # only 7Timer
    transparency_mag: float | None
    visibility_m: float | None  # Open-Meteo
    temperature_c: float | None
    relative_humidity_pct: float | None
    contributing_providers: tuple[str, ...]


class _Provider(Protocol):
    name: str

    def fetch(self, latitude: float, longitude: float) -> list:  # pragma: no cover - Protocol
        ...


@dataclass(slots=True)
class ConditionsAggregator:
    """Fetches and reconciles three providers into hour-keyed forecasts."""

    seven_timer: SevenTimerProvider = field(default_factory=SevenTimerProvider)
    nws: NWSProvider = field(default_factory=NWSProvider)
    open_meteo: OpenMeteoProvider = field(default_factory=OpenMeteoProvider)
    cache: ConditionsCache | None = None

    def fetch(self, latitude: float, longitude: float) -> list[ConditionsForecast]:
        """Fetch from all three providers and return the merged hourly forecast."""
        seven_slots = self._safe_fetch(self.seven_timer, latitude, longitude)
        nws_slots = self._safe_fetch(self.nws, latitude, longitude)
        meteo_slots = self._safe_fetch(self.open_meteo, latitude, longitude)

        if not (seven_slots or nws_slots or meteo_slots):
            raise AllProvidersDownError(
                "All three weather providers (7Timer, NOAA, Open-Meteo) failed."
            )

        # Buckets keyed by top-of-hour UTC datetime.
        buckets: dict[datetime, dict[str, Any]] = {}

        if seven_slots:
            for s in seven_slots:
                _expand_seven_timer(buckets, s)
        if nws_slots:
            for s in nws_slots:
                _absorb_nws(buckets, s)
        if meteo_slots:
            for s in meteo_slots:
                _absorb_meteo(buckets, s)

        forecasts = sorted(
            (_finalize(b) for b in buckets.values()),
            key=lambda f: f.hour_utc,
        )
        return forecasts

    def _safe_fetch(self, provider: _Provider, lat: float, lon: float) -> list:
        cache_key = f"{provider.name}:{lat:.4f},{lon:.4f}"
        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        try:
            data = provider.fetch(lat, lon)
        except Exception as exc:
            log.warning("provider %s failed: %s", provider.name, exc)
            return []
        if self.cache is not None and data:
            self.cache.set(cache_key, data)
        return data


def _hour_floor(dt: datetime) -> datetime:
    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    return dt.replace(minute=0, second=0, microsecond=0)


def _expand_seven_timer(buckets: dict[datetime, dict[str, Any]], slot: SevenTimerSlot) -> None:
    """7Timer reports every 3 hours; we replicate the values across each of those 3 hours."""
    base = _hour_floor(slot.timestamp_utc)
    for offset in range(3):
        hr = base + timedelta(hours=offset)
        b = buckets.setdefault(hr, _empty_bucket(hr))
        _bump_max(b, "cloud_cover_pct", slot.cloud_cover_pct)
        _bump_max(b, "wind_speed_mps", slot.wind10m_mps)
        b["seeing_arcsec"] = slot.seeing_arcsec
        b["transparency_mag"] = slot.transparency_mag
        if b.get("temperature_c") is None:
            b["temperature_c"] = slot.temperature_c
        if b.get("relative_humidity_pct") is None:
            b["relative_humidity_pct"] = slot.relative_humidity_pct
        _add_provider(b, "7timer")


def _absorb_nws(buckets: dict[datetime, dict[str, Any]], slot: NWSSlot) -> None:
    hr = _hour_floor(slot.start_utc)
    b = buckets.setdefault(hr, _empty_bucket(hr))
    if slot.cloud_cover_pct is not None:
        _bump_max(b, "cloud_cover_pct", slot.cloud_cover_pct)
    _bump_max(b, "wind_speed_mps", slot.wind_speed_mps)
    if b.get("temperature_c") is None:
        b["temperature_c"] = slot.temperature_c
    _add_provider(b, "nws")


def _absorb_meteo(buckets: dict[datetime, dict[str, Any]], slot: OpenMeteoSlot) -> None:
    hr = _hour_floor(slot.timestamp_utc)
    b = buckets.setdefault(hr, _empty_bucket(hr))
    _bump_max(b, "cloud_cover_pct", slot.cloud_cover_pct)
    _bump_max(b, "wind_speed_mps", slot.wind_speed_mps)
    b["visibility_m"] = slot.visibility_m
    _add_provider(b, "open-meteo")


def _empty_bucket(hr: datetime) -> dict[str, Any]:
    return {
        "hour_utc": hr,
        "cloud_cover_pct": 0.0,
        "wind_speed_mps": 0.0,
        "seeing_arcsec": None,
        "transparency_mag": None,
        "visibility_m": None,
        "temperature_c": None,
        "relative_humidity_pct": None,
        "providers": set(),
    }


def _bump_max(bucket: dict[str, Any], key: str, value: float) -> None:
    current = bucket.get(key)
    if current is None or value > current:
        bucket[key] = value


def _add_provider(bucket: dict[str, Any], name: str) -> None:
    bucket["providers"].add(name)


def _finalize(bucket: dict[str, Any]) -> ConditionsForecast:
    return ConditionsForecast(
        hour_utc=bucket["hour_utc"],
        cloud_cover_pct=float(bucket["cloud_cover_pct"]),
        wind_speed_mps=float(bucket["wind_speed_mps"]),
        seeing_arcsec=bucket["seeing_arcsec"],
        transparency_mag=bucket["transparency_mag"],
        visibility_m=bucket["visibility_m"],
        temperature_c=bucket["temperature_c"],
        relative_humidity_pct=bucket["relative_humidity_pct"],
        contributing_providers=tuple(sorted(bucket["providers"])),
    )


# ---- Convenience wrappers ----------------------------------------------------------------


def fetch_forecast(
    latitude: float,
    longitude: float,
    *,
    aggregator: ConditionsAggregator | None = None,
) -> list[ConditionsForecast]:
    """Fetch the merged hourly forecast for a site."""
    agg = aggregator or ConditionsAggregator()
    return agg.fetch(latitude, longitude)


def fetch_current_conditions(
    latitude: float,
    longitude: float,
    *,
    aggregator: ConditionsAggregator | None = None,
    now: datetime | None = None,
) -> ConditionsForecast | None:
    """Return the forecast bucket covering ``now`` (default: real now in UTC)."""
    forecasts = fetch_forecast(latitude, longitude, aggregator=aggregator)
    target = _hour_floor(now or datetime.now(UTC))
    for f in forecasts:
        if f.hour_utc == target:
            return f
    return forecasts[0] if forecasts else None
