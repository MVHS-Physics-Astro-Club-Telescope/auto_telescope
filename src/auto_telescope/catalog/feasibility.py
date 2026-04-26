"""Feasibility check: can the 10" + ASI120MC-S realistically image this?

We model three independent constraints:

1. **Magnitude floor** — anything fainter than mag ~12 is below SNR for 30-s exposures
   on this rig at MVHS skies (Bortle 7).
2. **Angular size** — the ASI120MC-S FOV at f=1140mm is ~14'×11'. Targets larger than
   this can still be observed but only in fragments; we down-rank them.
3. **Declination** — at +37 deg, anything south of dec ~-30 deg never rises above the
   safety horizon (20 deg). Hard reject.

Each rejection comes with a human-readable reason for the operator UI.
"""

from __future__ import annotations

from dataclasses import dataclass

from auto_telescope.catalog.targets import Target, Tier
from auto_telescope.config.site import Site

# ZWO ASI120MC-S sensor (4.8mm x 3.6mm) at f = 1140 mm gives FOV ~14.5' x 10.85'.
CAMERA_FOV_WIDTH_ARCMIN = 14.5
CAMERA_FOV_HEIGHT_ARCMIN = 10.85

# At Bortle 7 with 30s unguided exposures, 12.0 mag is roughly the SNR floor.
DEFAULT_MAG_LIMIT = 12.0


@dataclass(frozen=True, slots=True)
class FeasibilityVerdict:
    """Whether a target is feasible from this site, with explanation."""

    feasible: bool
    reason: str
    notes: tuple[str, ...] = ()


def assess_feasibility(
    target: Target,
    *,
    site: Site,
    magnitude_limit: float = DEFAULT_MAG_LIMIT,
    safety_horizon_deg: float = 20.0,
) -> FeasibilityVerdict:
    """Decide whether this target should ever be attempted from this site."""
    notes: list[str] = []

    # --- Tier explicit reject ---
    if target.tier == Tier.SKIP:
        return FeasibilityVerdict(
            feasible=False,
            reason=f"target tier=SKIP ({target.description or 'curated rejection'})",
        )

    # --- Magnitude floor ---
    if target.magnitude is not None and target.magnitude > magnitude_limit:
        return FeasibilityVerdict(
            feasible=False,
            reason=(
                f"mag {target.magnitude:.1f} fainter than detection limit "
                f"{magnitude_limit:.1f} for 30-s exposures at Bortle 7"
            ),
        )

    # --- Declination / horizon constraint ---
    # Max altitude at upper culmination: 90 - |lat - dec|.
    max_altitude = 90.0 - abs(site.latitude - target.dec_deg)
    if max_altitude < safety_horizon_deg:
        return FeasibilityVerdict(
            feasible=False,
            reason=(
                f"max altitude from {site.name} is {max_altitude:.1f} deg, "
                f"below safety horizon {safety_horizon_deg:.0f} deg"
            ),
        )

    # --- Angular size note (does not block, just informs) ---
    size = target.angular_size_arcmin
    if size is not None:
        if size > CAMERA_FOV_WIDTH_ARCMIN:
            notes.append(
                f"target spans {size:.1f}' but FOV is {CAMERA_FOV_WIDTH_ARCMIN:.1f}'; "
                "image will be cropped to a region of interest"
            )
        elif size < 0.5:
            notes.append("target is < 0.5' — point-source / star-like at our resolution")

    return FeasibilityVerdict(feasible=True, reason="ok", notes=tuple(notes))
