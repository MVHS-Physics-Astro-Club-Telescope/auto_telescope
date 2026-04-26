"""Hard interlocks that prevent the telescope from damaging itself.

Design principles:
  * Fail closed: any uncertainty (None forecast, exception, missing data) → refuse.
  * Independent checks: each interlock is its own function so tests can target it.
  * Conservative defaults: 30 deg sun avoidance, 20 deg horizon, 15 m/s wind.

Every public ``check_*`` returns an ``InterlockResult``. The aggregate
``check_can_slew`` runs all of them and refuses on the first failure (so the
operator UI gets the most-actionable reason).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from auto_telescope.conditions.aggregator import ConditionsForecast
from auto_telescope.config.settings import Settings, get_settings
from auto_telescope.config.site import Site
from auto_telescope.visibility.coordinates import (
    EquatorialCoord,
    angular_separation_deg,
    radec_to_altaz,
)
from auto_telescope.visibility.horizons import sun_altitude


class SafetyError(RuntimeError):
    """Raised when an unrecoverable safety condition is detected."""


@dataclass(frozen=True, slots=True)
class InterlockResult:
    """Outcome of a single interlock check."""

    safe: bool
    code: str
    detail: str

    @classmethod
    def ok(cls, code: str = "ok", detail: str = "") -> InterlockResult:
        return cls(safe=True, code=code, detail=detail)

    @classmethod
    def deny(cls, code: str, detail: str) -> InterlockResult:
        return cls(safe=False, code=code, detail=detail)


def check_sun_avoidance(
    target: EquatorialCoord,
    *,
    when_utc: datetime,
    site: Site,
    min_separation_deg: float,
) -> InterlockResult:
    """Refuse if the target is within ``min_separation_deg`` of the sun (any altitude)."""
    if when_utc.tzinfo is None:
        when_utc = when_utc.replace(tzinfo=UTC)

    sun_pos = sun_altitude(when_utc, site)
    target_pos = radec_to_altaz(target, when_utc, site)
    if target_pos.altitude_deg < -90.0 or target_pos.altitude_deg > 90.0:
        return InterlockResult.deny("invalid_target_altitude", "target altitude out of range")

    # Robust separation: convert both to RA/Dec and compute great-circle distance.
    from astropy import units as u
    from astropy.coordinates import AltAz, SkyCoord
    from astropy.time import Time

    t = Time(when_utc.astimezone(UTC))
    altaz_frame = AltAz(obstime=t, location=site.to_earth_location())
    sun_skycoord = SkyCoord(
        alt=sun_pos.altitude_deg * u.deg, az=sun_pos.azimuth_deg * u.deg, frame=altaz_frame
    ).transform_to("icrs")
    sun_radec = EquatorialCoord(
        ra_deg=float(sun_skycoord.ra.to(u.deg).value) % 360.0,
        dec_deg=float(sun_skycoord.dec.to(u.deg).value),
    )

    sep = angular_separation_deg(target, sun_radec)
    if sep < min_separation_deg:
        return InterlockResult.deny(
            "sun_too_close",
            f"target {sep:.1f} deg from sun (min {min_separation_deg:.0f})",
        )
    return InterlockResult.ok("sun_ok", f"target {sep:.1f} deg from sun")


def check_horizon(
    target: EquatorialCoord,
    *,
    when_utc: datetime,
    site: Site,
    min_altitude_deg: float,
) -> InterlockResult:
    """Refuse if target is below ``min_altitude_deg`` (avoids slewing into walls/trees)."""
    pos = radec_to_altaz(target, when_utc, site)
    if pos.altitude_deg < min_altitude_deg:
        return InterlockResult.deny(
            "below_horizon",
            f"target altitude {pos.altitude_deg:.1f} deg < min {min_altitude_deg:.1f}",
        )
    return InterlockResult.ok("horizon_ok", f"target altitude {pos.altitude_deg:.1f} deg")


def check_wind(
    forecast: ConditionsForecast | None,
    *,
    max_wind_speed_mps: float,
) -> InterlockResult:
    """Refuse if forecast wind exceeds the safe threshold (or if forecast missing)."""
    if forecast is None:
        return InterlockResult.deny("no_forecast", "no weather forecast available; refusing")
    if forecast.wind_speed_mps > max_wind_speed_mps:
        return InterlockResult.deny(
            "wind_too_high",
            f"wind {forecast.wind_speed_mps:.1f} m/s > max {max_wind_speed_mps:.1f}",
        )
    return InterlockResult.ok("wind_ok", f"wind {forecast.wind_speed_mps:.1f} m/s")


@dataclass(frozen=True, slots=True)
class SafetyInterlocks:
    """Bundles all interlock thresholds for repeated calls."""

    site: Site
    sun_avoidance_deg: float
    min_altitude_deg: float
    max_wind_speed_mps: float

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> SafetyInterlocks:
        s = settings or get_settings()
        return cls(
            site=s.to_site(),
            sun_avoidance_deg=s.sun_avoidance_deg,
            min_altitude_deg=s.min_altitude_deg,
            max_wind_speed_mps=s.max_wind_speed_mps,
        )

    def check(
        self,
        target: EquatorialCoord,
        *,
        when_utc: datetime,
        forecast: ConditionsForecast | None,
    ) -> list[InterlockResult]:
        """Run every check and return all results."""
        return [
            check_sun_avoidance(
                target,
                when_utc=when_utc,
                site=self.site,
                min_separation_deg=self.sun_avoidance_deg,
            ),
            check_horizon(
                target,
                when_utc=when_utc,
                site=self.site,
                min_altitude_deg=self.min_altitude_deg,
            ),
            check_wind(forecast, max_wind_speed_mps=self.max_wind_speed_mps),
        ]


def check_can_slew(
    target: EquatorialCoord,
    *,
    when_utc: datetime,
    site: Site | None = None,
    forecast: ConditionsForecast | None = None,
    settings: Settings | None = None,
) -> InterlockResult:
    """One-call safety check used by all slew sites in the controller.

    Returns the FIRST failure (so callers can render a single, actionable reason).
    Returns InterlockResult.ok if every check passes.
    """
    s = settings or get_settings()
    locks = SafetyInterlocks(
        site=site or s.to_site(),
        sun_avoidance_deg=s.sun_avoidance_deg,
        min_altitude_deg=s.min_altitude_deg,
        max_wind_speed_mps=s.max_wind_speed_mps,
    )
    for result in locks.check(target, when_utc=when_utc, forecast=forecast):
        if not result.safe:
            return result
    return InterlockResult.ok("all_clear", "all interlocks passed")
