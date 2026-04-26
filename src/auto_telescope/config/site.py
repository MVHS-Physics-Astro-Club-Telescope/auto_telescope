"""Observing site definition.

The default site is Mountain View High School (MVHS) in Mountain View, CA, where the
telescope is permanently housed. Coordinates are taken from the design doc (v3.1) and
chosen to be the rooftop platform centroid.

Sites are immutable value objects. To override, construct a new Site or set the
`AUTO_TELESCOPE_LATITUDE` / `_LONGITUDE` / `_ELEVATION_M` env vars (see settings.py).
"""

from __future__ import annotations

from dataclasses import dataclass

from astropy import units as u
from astropy.coordinates import EarthLocation


@dataclass(frozen=True, slots=True)
class Site:
    """An observing location on Earth.

    Attributes:
        name:        Human-readable site name.
        latitude:    Geodetic latitude in decimal degrees (north positive).
        longitude:   Geodetic longitude in decimal degrees (east positive, west negative).
        elevation_m: Site elevation above mean sea level, in meters.
        timezone:    IANA timezone identifier (e.g. "America/Los_Angeles").
    """

    name: str
    latitude: float
    longitude: float
    elevation_m: float
    timezone: str = "America/Los_Angeles"

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError(f"latitude must be in [-90, 90]; got {self.latitude}")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError(f"longitude must be in [-180, 180]; got {self.longitude}")
        if self.elevation_m < -500.0 or self.elevation_m > 9000.0:
            raise ValueError(
                f"elevation_m looks wrong (Mt. Everest = 8849m); got {self.elevation_m}"
            )

    def to_earth_location(self) -> EarthLocation:
        """Convert to an astropy EarthLocation for use in coordinate transforms."""
        return EarthLocation(
            lat=self.latitude * u.deg,
            lon=self.longitude * u.deg,
            height=self.elevation_m * u.m,
        )


# Default site: MVHS rooftop platform, Mountain View, CA.
# Source: design doc v3.1; rounded to 0.001 deg (~110 m precision, fine for visibility math).
MVHS_SITE: Site = Site(
    name="Mountain View High School",
    latitude=37.366,
    longitude=-122.077,
    elevation_m=30.0,
    timezone="America/Los_Angeles",
)
