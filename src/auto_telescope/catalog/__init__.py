"""Smart catalog: ~80 curated targets + SIMBAD lookups + solar-system ephemerides."""

from auto_telescope.catalog.curated import CURATED_TARGETS, get_curated_target
from auto_telescope.catalog.feasibility import (
    FeasibilityVerdict,
    assess_feasibility,
)
from auto_telescope.catalog.simbad import lookup_simbad
from auto_telescope.catalog.solar_system import (
    SOLAR_SYSTEM_BODIES,
    is_solar_system_body,
    lookup_solar_system,
)
from auto_telescope.catalog.targets import Target, TargetType, Tier, resolve_target

__all__ = [
    "CURATED_TARGETS",
    "SOLAR_SYSTEM_BODIES",
    "FeasibilityVerdict",
    "Target",
    "TargetType",
    "Tier",
    "assess_feasibility",
    "get_curated_target",
    "is_solar_system_body",
    "lookup_simbad",
    "lookup_solar_system",
    "resolve_target",
]
