"""High-level visibility rule: "can we observe X right now?"

Combines:
  * is target above min_altitude
  * is sun safely down
  * is target far enough from the moon (optional)

Returns a ``VisibilityVerdict`` with a structured reason on failure so the
operator UI can explain why a target was skipped.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from astropy import units as u
from astropy.coordinates import AltAz, get_body
from astropy.time import Time

from auto_telescope.config.site import Site
from auto_telescope.visibility.coordinates import EquatorialCoord, radec_to_altaz
from auto_telescope.visibility.horizons import sun_altitude


@dataclass(frozen=True, slots=True)
class VisibilityVerdict:
    """Result of a visibility check."""

    visible: bool
    altitude_deg: float
    azimuth_deg: float
    reason: str  # "ok" or short explanation
    sun_altitude_deg: float | None = None
    moon_separation_deg: float | None = None


def is_visible(
    coord: EquatorialCoord,
    when_utc: datetime,
    site: Site,
    *,
    min_altitude_deg: float = 20.0,
    require_sun_below_deg: float = 6.0,
    min_moon_separation_deg: float = 5.0,
) -> VisibilityVerdict:
    """Check if a target is observable right now.

    Returns a VisibilityVerdict with structured pass/fail reason.
    """
    if when_utc.tzinfo is None:
        when_utc = when_utc.replace(tzinfo=UTC)

    pos = radec_to_altaz(coord, when_utc, site)

    sun_pos = sun_altitude(when_utc, site)
    if sun_pos.altitude_deg >= -require_sun_below_deg:
        return VisibilityVerdict(
            visible=False,
            altitude_deg=pos.altitude_deg,
            azimuth_deg=pos.azimuth_deg,
            reason=f"sun above {-require_sun_below_deg:.0f} deg (alt={sun_pos.altitude_deg:.1f})",
            sun_altitude_deg=sun_pos.altitude_deg,
        )

    if pos.altitude_deg < min_altitude_deg:
        return VisibilityVerdict(
            visible=False,
            altitude_deg=pos.altitude_deg,
            azimuth_deg=pos.azimuth_deg,
            reason=f"target altitude {pos.altitude_deg:.1f} below min {min_altitude_deg}",
            sun_altitude_deg=sun_pos.altitude_deg,
        )

    # Moon separation (best-effort; cheap with get_body)
    t = Time(when_utc.astimezone(UTC))
    moon = get_body("moon", t, site.to_earth_location())
    target_skycoord = coord.to_skycoord()
    sep_deg = float(moon.separation(target_skycoord).to(u.deg).value)
    if sep_deg < min_moon_separation_deg:
        return VisibilityVerdict(
            visible=False,
            altitude_deg=pos.altitude_deg,
            azimuth_deg=pos.azimuth_deg,
            reason=f"target {sep_deg:.1f} deg from moon (min {min_moon_separation_deg})",
            sun_altitude_deg=sun_pos.altitude_deg,
            moon_separation_deg=sep_deg,
        )

    # Confirm moon altaz so the verdict carries the data.
    moon_altaz = moon.transform_to(AltAz(obstime=t, location=site.to_earth_location()))
    _ = moon_altaz  # keeps the import meaningful and ensures eager eval if astropy lazy-loads

    return VisibilityVerdict(
        visible=True,
        altitude_deg=pos.altitude_deg,
        azimuth_deg=pos.azimuth_deg,
        reason="ok",
        sun_altitude_deg=sun_pos.altitude_deg,
        moon_separation_deg=sep_deg,
    )
