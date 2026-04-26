"""Celestial coordinate transforms wrapping astropy.

We expose tiny dataclasses (EquatorialCoord, AltAzPosition) so callers don't have
to depend on astropy types directly. Round-tripping ``radec_to_altaz`` →
``altaz_to_radec`` must be lossless within ~arcsec; this is asserted by a
property test.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time

from auto_telescope.config.site import Site


@dataclass(frozen=True, slots=True)
class EquatorialCoord:
    """An equatorial (RA/Dec) sky position, ICRS frame, J2000."""

    ra_deg: float  # 0..360
    dec_deg: float  # -90..90

    def __post_init__(self) -> None:
        if not 0.0 <= self.ra_deg < 360.0:
            # Allow exactly 360 — wrap.
            object.__setattr__(self, "ra_deg", self.ra_deg % 360.0)
        if not -90.0 <= self.dec_deg <= 90.0:
            raise ValueError(f"dec_deg out of range [-90,90]: {self.dec_deg}")

    def to_skycoord(self) -> SkyCoord:
        return SkyCoord(ra=self.ra_deg * u.deg, dec=self.dec_deg * u.deg, frame="icrs")


@dataclass(frozen=True, slots=True)
class AltAzPosition:
    """A horizontal (Alt/Az) sky position at a specific time and site."""

    altitude_deg: float  # -90..90; negative = below horizon
    azimuth_deg: float  # 0..360; 0 = north, 90 = east
    when_utc: datetime
    site_name: str

    def __post_init__(self) -> None:
        if not -90.0 <= self.altitude_deg <= 90.0:
            raise ValueError(f"altitude out of range: {self.altitude_deg}")
        # Wrap az into [0,360)
        object.__setattr__(self, "azimuth_deg", self.azimuth_deg % 360.0)


def _earth_location(site: Site) -> EarthLocation:
    return site.to_earth_location()


def radec_to_altaz(coord: EquatorialCoord, when_utc: datetime, site: Site) -> AltAzPosition:
    """Transform RA/Dec → Alt/Az for a given site and UTC instant."""
    if when_utc.tzinfo is None:
        when_utc = when_utc.replace(tzinfo=UTC)
    t = Time(when_utc.astimezone(UTC))
    altaz_frame = AltAz(obstime=t, location=_earth_location(site))
    transformed = coord.to_skycoord().transform_to(altaz_frame)
    return AltAzPosition(
        altitude_deg=float(transformed.alt.to(u.deg).value),
        azimuth_deg=float(transformed.az.to(u.deg).value),
        when_utc=when_utc,
        site_name=site.name,
    )


def altaz_to_radec(position: AltAzPosition, site: Site) -> EquatorialCoord:
    """Inverse of :func:`radec_to_altaz`."""
    when = position.when_utc
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    t = Time(when.astimezone(UTC))
    altaz_frame = AltAz(obstime=t, location=_earth_location(site))
    altaz_coord = SkyCoord(
        alt=position.altitude_deg * u.deg,
        az=position.azimuth_deg * u.deg,
        frame=altaz_frame,
    )
    icrs = altaz_coord.transform_to("icrs")
    return EquatorialCoord(
        ra_deg=float(icrs.ra.to(u.deg).value) % 360.0,
        dec_deg=float(icrs.dec.to(u.deg).value),
    )


def angular_separation_deg(a: EquatorialCoord, b: EquatorialCoord) -> float:
    """Great-circle angular separation between two equatorial coords, in degrees."""
    return float(a.to_skycoord().separation(b.to_skycoord()).to(u.deg).value)


def slew_distance_deg(a: AltAzPosition, b: AltAzPosition) -> float:
    """Approximate slew distance between two alt-az positions, on the unit sphere.

    Used by the scheduler to penalize long slews. Symmetry is asserted by a property test.
    """
    a1 = np.radians(a.altitude_deg)
    a2 = np.radians(b.altitude_deg)
    daz = np.radians(((b.azimuth_deg - a.azimuth_deg + 540.0) % 360.0) - 180.0)
    cos_d = np.sin(a1) * np.sin(a2) + np.cos(a1) * np.cos(a2) * np.cos(daz)
    cos_d = max(-1.0, min(1.0, float(cos_d)))
    return float(np.degrees(np.arccos(cos_d)))
