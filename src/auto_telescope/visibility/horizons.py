"""Horizon checks: is X above the horizon? Is the sun safely down?

We use civil-twilight semantics by default: the sun must be at least 6 deg below the
horizon for "night". This is configurable per call.
"""

from __future__ import annotations

from datetime import UTC, datetime

from astropy import units as u
from astropy.coordinates import AltAz, get_sun
from astropy.time import Time

from auto_telescope.config.site import Site
from auto_telescope.visibility.coordinates import (
    AltAzPosition,
    EquatorialCoord,
    radec_to_altaz,
)


def is_above_horizon(
    coord: EquatorialCoord,
    when_utc: datetime,
    site: Site,
    *,
    min_altitude_deg: float = 0.0,
) -> bool:
    """True if the target is at or above ``min_altitude_deg`` at ``when_utc``."""
    p = radec_to_altaz(coord, when_utc, site)
    return p.altitude_deg >= min_altitude_deg


def sun_altitude(when_utc: datetime, site: Site) -> AltAzPosition:
    """Return the Sun's altitude at the given moment."""
    if when_utc.tzinfo is None:
        when_utc = when_utc.replace(tzinfo=UTC)
    t = Time(when_utc.astimezone(UTC))
    sun_icrs = get_sun(t)
    altaz = sun_icrs.transform_to(AltAz(obstime=t, location=site.to_earth_location()))
    return AltAzPosition(
        altitude_deg=float(altaz.alt.to(u.deg).value),
        azimuth_deg=float(altaz.az.to(u.deg).value),
        when_utc=when_utc,
        site_name=site.name,
    )


def sun_below_horizon(
    when_utc: datetime,
    site: Site,
    *,
    twilight_deg: float = 6.0,
) -> bool:
    """True if the sun is at least ``twilight_deg`` below the horizon (civil twilight default).

    Astronomical twilight = 18 deg, nautical = 12 deg, civil = 6 deg. The default of 6 deg
    matches "the sky is dark enough to start observing bright targets." Faint deep-sky
    work should pass twilight_deg=18.
    """
    return sun_altitude(when_utc, site).altitude_deg < -twilight_deg
