"""Solar system body lookups via astropy.coordinates.get_body.

For Sun/Moon/planets we use the local builtin ephemeris (no network). For asteroids
and comets the user can fall through to JPL Horizons via astroquery — that path is
covered separately in catalog.simbad-style helpers, but for Phase 1A the planets and
Moon are sufficient.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from astropy import units as u
from astropy.coordinates import EarthLocation, get_body, get_sun
from astropy.time import Time

from auto_telescope.catalog.targets import Target, TargetType, Tier
from auto_telescope.config.site import MVHS_SITE, Site

# Canonical names → ID + display name + tier.
SOLAR_SYSTEM_BODIES: dict[str, dict[str, Any]] = {
    "sun": {
        "id": "sun",
        "display_name": "Sun",
        "target_type": TargetType.SUN,
        "tier": Tier.SKIP,  # Never observe without solar filter — safety blocks anyway.
        "description": "DO NOT OBSERVE without a certified solar filter.",
    },
    "moon": {
        "id": "moon",
        "display_name": "Moon",
        "target_type": TargetType.MOON,
        "tier": Tier.EASY,
        "description": "Earth's moon. Spectacular at any phase; first quarter shows the most relief.",
    },
    "mercury": {
        "id": "mercury",
        "display_name": "Mercury",
        "target_type": TargetType.PLANET,
        "tier": Tier.CHALLENGING,
        "description": "Innermost planet; small phase and always near the sun. Skip unless near elongation.",
    },
    "venus": {
        "id": "venus",
        "display_name": "Venus",
        "target_type": TargetType.PLANET,
        "tier": Tier.EASY,
        "description": "Brightest planet. Shows phases like the moon. Best near greatest elongation.",
    },
    "mars": {
        "id": "mars",
        "display_name": "Mars",
        "target_type": TargetType.PLANET,
        "tier": Tier.EASY,
        "description": "Red planet. Polar caps + dark surface markings visible near opposition.",
    },
    "jupiter": {
        "id": "jupiter",
        "display_name": "Jupiter",
        "target_type": TargetType.PLANET,
        "tier": Tier.EASY,
        "description": "Easy showpiece. Cloud bands, GRS, four Galilean moons in a single FOV.",
    },
    "saturn": {
        "id": "saturn",
        "display_name": "Saturn",
        "target_type": TargetType.PLANET,
        "tier": Tier.EASY,
        "description": "The crowd favorite. Ring system + Cassini Division at high power.",
    },
    "uranus": {
        "id": "uranus",
        "display_name": "Uranus",
        "target_type": TargetType.PLANET,
        "tier": Tier.CHALLENGING,
        "description": "Tiny blue-green disk. No detail at our aperture; identification only.",
    },
    "neptune": {
        "id": "neptune",
        "display_name": "Neptune",
        "target_type": TargetType.PLANET,
        "tier": Tier.CHALLENGING,
        "description": "Stellar except at high power. Triton barely detectable.",
    },
}

_ALIASES = {
    "the sun": "sun",
    "sol": "sun",
    "the moon": "moon",
    "luna": "moon",
}


def is_solar_system_body(name: str) -> bool:
    """True if ``name`` matches a known solar-system body (case-insensitive)."""
    key = name.strip().lower()
    return key in SOLAR_SYSTEM_BODIES or key in _ALIASES


def _canonical(name: str) -> str:
    key = name.strip().lower()
    return _ALIASES.get(key, key)


def lookup_solar_system(
    name: str,
    *,
    when_utc: datetime | None = None,
    site: Site | None = None,
) -> Target:
    """Return a Target for a solar-system body, with current RA/Dec at ``when_utc``.

    Args:
        name:    Body name (e.g. "Jupiter", "moon", case-insensitive).
        when_utc: Time to evaluate ephemeris at (default: now UTC).
        site:    Observing site for topocentric correction (default: MVHS).
    """
    key = _canonical(name)
    if key not in SOLAR_SYSTEM_BODIES:
        raise KeyError(f"{name!r} is not a recognized solar-system body")
    spec = SOLAR_SYSTEM_BODIES[key]

    when = when_utc or datetime.now(UTC)
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    site = site or MVHS_SITE

    location: EarthLocation = site.to_earth_location()
    t = Time(when.astimezone(UTC))

    body = get_sun(t) if key == "sun" else get_body(key, t, location)

    ra_deg = float(body.ra.to(u.deg).value) % 360.0
    dec_deg = float(body.dec.to(u.deg).value)

    return Target(
        id=str(spec["id"]),
        display_name=str(spec["display_name"]),
        target_type=spec["target_type"],
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        magnitude=None,
        angular_size_arcmin=None,
        tier=spec["tier"],
        best_months=tuple(range(1, 13)),  # solar bodies move; "any month" is fine
        description=str(spec.get("description", "")),
    )
