"""Target schema + universal resolver.

A ``Target`` is the unified representation of any observable thing:
solar system bodies, deep-sky objects, double stars. Coordinates are RA/Dec
at J2000 ICRS for fixed targets; for solar system bodies, ra_deg/dec_deg are
recomputed at request time and the dataclass carries placeholder zeros.

``resolve_target(name)`` is the front door:
  1. Solar-system body? → solar_system.lookup_solar_system
  2. In curated list?    → curated.get_curated_target
  3. Otherwise            → simbad.lookup_simbad (network)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum

from auto_telescope.config.site import Site
from auto_telescope.visibility.coordinates import EquatorialCoord


class TargetType(StrEnum):
    """Enumeration of supported target types."""

    PLANET = "planet"
    MOON = "moon"
    SUN = "sun"  # Never observed; included so safety can recognize it.
    GLOBULAR_CLUSTER = "globular_cluster"
    OPEN_CLUSTER = "open_cluster"
    PLANETARY_NEBULA = "planetary_nebula"
    EMISSION_NEBULA = "emission_nebula"
    REFLECTION_NEBULA = "reflection_nebula"
    SUPERNOVA_REMNANT = "supernova_remnant"
    GALAXY = "galaxy"
    DOUBLE_STAR = "double_star"
    STAR = "star"
    ASTERISM = "asterism"
    OTHER = "other"


class Tier(int, Enum):
    """Difficulty tier for the 10" Dobsonian + ASI120MC-S camera at MVHS skies."""

    EASY = 1  # bright, large, beginner-friendly
    CHALLENGING = 2  # visible but needs clear skies + experience
    SKIP = 3  # auto-rejected with explanation


@dataclass(frozen=True, slots=True)
class Target:
    """An observable target with metadata for scheduling + display."""

    id: str
    display_name: str
    target_type: TargetType
    ra_deg: float  # 0..360 (J2000 ICRS for fixed targets)
    dec_deg: float  # -90..90
    magnitude: float | None  # Visual magnitude; None for solar bodies (varies)
    angular_size_arcmin: float | None
    tier: Tier
    best_months: tuple[int, ...] = field(
        default_factory=tuple
    )  # 1..12, when on the meridian at evening
    description: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)

    def equatorial(self) -> EquatorialCoord:
        return EquatorialCoord(ra_deg=self.ra_deg % 360.0, dec_deg=self.dec_deg)


def resolve_target(
    name: str,
    *,
    when_utc: datetime | None = None,
    site: Site | None = None,
) -> Target:
    """Look up a target by name from any source.

    Resolution order:
      1. Solar system body (fast, local — astropy ephemeris).
      2. Curated catalog (fast, in-memory).
      3. SIMBAD (network call).

    Raises:
        KeyError: if the name resolves to nothing in any source.
    """
    # Imports inside the function to avoid circular imports at module load time.
    from auto_telescope.catalog.curated import get_curated_target
    from auto_telescope.catalog.simbad import lookup_simbad
    from auto_telescope.catalog.solar_system import (
        is_solar_system_body,
        lookup_solar_system,
    )

    if is_solar_system_body(name):
        return lookup_solar_system(name, when_utc=when_utc, site=site)

    curated = get_curated_target(name)
    if curated is not None:
        return curated

    simbad = lookup_simbad(name)
    if simbad is not None:
        return simbad

    raise KeyError(f"target {name!r} not found in solar system, curated catalog, or SIMBAD")
