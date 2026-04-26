"""Safety interlocks. The single most important module in the codebase.

Top fear: telescope damages itself unattended (slews into the sun, drives below
the horizon into a wall, runs the motors past hard stops). Every public function
here is fail-CLOSED: any unknown input → refuse to slew.
"""

from auto_telescope.safety.interlocks import (
    InterlockResult,
    SafetyError,
    SafetyInterlocks,
    check_can_slew,
)

__all__ = [
    "InterlockResult",
    "SafetyError",
    "SafetyInterlocks",
    "check_can_slew",
]
