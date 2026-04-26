"""Visibility module: celestial coordinate transforms + horizon/altitude windows.

Pure-local computations using astropy. No network access.
"""

from auto_telescope.visibility.coordinates import (
    AltAzPosition,
    EquatorialCoord,
    altaz_to_radec,
    angular_separation_deg,
    radec_to_altaz,
)
from auto_telescope.visibility.horizons import (
    is_above_horizon,
    sun_altitude,
    sun_below_horizon,
)
from auto_telescope.visibility.rules import (
    VisibilityVerdict,
    is_visible,
)
from auto_telescope.visibility.windows import (
    VisibilityWindow,
    compute_windows,
)

__all__ = [
    "AltAzPosition",
    "EquatorialCoord",
    "VisibilityVerdict",
    "VisibilityWindow",
    "altaz_to_radec",
    "angular_separation_deg",
    "compute_windows",
    "is_above_horizon",
    "is_visible",
    "radec_to_altaz",
    "sun_altitude",
    "sun_below_horizon",
]
