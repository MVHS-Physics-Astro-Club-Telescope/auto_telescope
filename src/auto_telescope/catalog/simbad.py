"""SIMBAD lookup adapter (astroquery.simbad).

We isolate astroquery in this module so the rest of the codebase doesn't have to think
about VOTable types. SIMBAD outages are non-fatal: ``lookup_simbad`` returns ``None``
on failure and the resolver chain falls back / errors out at the call site.
"""

from __future__ import annotations

import logging
from typing import Any

from astropy import units as u
from astropy.coordinates import SkyCoord

from auto_telescope.catalog.targets import Target, TargetType, Tier

log = logging.getLogger(__name__)


_OTYPE_TO_TARGET_TYPE: dict[str, TargetType] = {
    # SIMBAD canonical otype codes.
    "GlC": TargetType.GLOBULAR_CLUSTER,
    "GlobCluster": TargetType.GLOBULAR_CLUSTER,
    "OpC": TargetType.OPEN_CLUSTER,
    "OpenCluster": TargetType.OPEN_CLUSTER,
    "PN": TargetType.PLANETARY_NEBULA,
    "PlanetaryNeb": TargetType.PLANETARY_NEBULA,
    "EmN": TargetType.EMISSION_NEBULA,
    "HII": TargetType.EMISSION_NEBULA,
    "RfN": TargetType.REFLECTION_NEBULA,
    "SNR": TargetType.SUPERNOVA_REMNANT,
    "SuperNovaRemnant": TargetType.SUPERNOVA_REMNANT,
    "G": TargetType.GALAXY,
    "Galaxy": TargetType.GALAXY,
    "**": TargetType.DOUBLE_STAR,
    "Double": TargetType.DOUBLE_STAR,
    "*": TargetType.STAR,
    "Star": TargetType.STAR,
}


def lookup_simbad(name: str) -> Target | None:
    """Query SIMBAD by object name. Returns ``None`` on miss or on network failure."""
    try:
        from astroquery.simbad import Simbad
    except Exception as exc:  # pragma: no cover - astroquery import error path
        log.warning("astroquery.simbad import failed: %s", exc)
        return None

    try:
        s = Simbad()
        # Modern astroquery (>=0.4.8) uses 'V' for visual magnitude and 'otype' for
        # object type. Older versions accepted 'flux(V)'. Try both for forward+back
        # compat; ignore unsupported fields.
        import contextlib

        for f in ("V", "otype", "dimensions"):
            with contextlib.suppress(Exception):
                s.add_votable_fields(f)
        result = s.query_object(name)
    except Exception as exc:
        log.warning("SIMBAD query for %r failed: %s", name, exc)
        return None

    if result is None or len(result) == 0:
        return None

    row = result[0]
    cols = row.colnames

    def _col(*names: str) -> object:
        for n in names:
            if n in cols:
                v = row[n]
                # astropy MaskedColumn entries can be masked; treat as None.
                try:
                    if hasattr(v, "mask") and v.mask:
                        return None
                except Exception:
                    pass
                return v
        return None

    ra: Any = _col("RA", "ra")
    dec: Any = _col("DEC", "dec")
    if ra is None or dec is None:
        return None

    coord: SkyCoord | None = None
    # Newer astroquery returns RA/Dec already in degrees as floats.
    try:
        coord = SkyCoord(ra=float(ra) * u.deg, dec=float(dec) * u.deg)
    except (TypeError, ValueError):
        try:
            coord = SkyCoord(f"{ra} {dec}", unit=(u.hourangle, u.deg))
        except Exception as exc:
            log.warning("SIMBAD coord parse failed for %r: %s", name, exc)
            return None

    otype_val = _col("OTYPE", "otype", "OTYPE_S", "main_type")
    otype = str(otype_val) if otype_val is not None else ""

    mag_val: Any = _col("FLUX_V", "flux_V", "V")
    magnitude: float | None
    try:
        magnitude = float(mag_val) if mag_val is not None else None
    except (TypeError, ValueError):
        magnitude = None

    return Target(
        id=name.strip(),
        display_name=name.strip(),
        target_type=_OTYPE_TO_TARGET_TYPE.get(otype, TargetType.OTHER),
        ra_deg=float(coord.ra.to(u.deg).value) % 360.0,
        dec_deg=float(coord.dec.to(u.deg).value),
        magnitude=magnitude,
        angular_size_arcmin=None,
        tier=Tier.CHALLENGING,  # unknown ⇒ assume challenging
        best_months=(),
        description=f"Resolved via SIMBAD (otype={otype}).",
    )
