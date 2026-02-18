from shared.enums.status_codes import StatusCode
from shared.state.telescope_state import TelescopeState

# Sample named targets with approximate coordinates
SAMPLE_TARGETS = [
    {"name": "Polaris", "ra": 37.95, "dec": 89.26, "alt": 37.4, "az": 0.1},
    {"name": "Sirius", "ra": 101.29, "dec": -16.72, "alt": 25.0, "az": 180.0},
    {"name": "Vega", "ra": 279.23, "dec": 38.78, "alt": 60.0, "az": 270.0},
    {"name": "Mars", "ra": 45.0, "dec": 20.0, "alt": 45.0, "az": 120.0},
    {"name": "Jupiter", "ra": 30.0, "dec": -5.0, "alt": 35.0, "az": 200.0},
]

# A slew sequence for testing movement
SLEW_SEQUENCE = [
    {"alt": 45.0, "az": 0.0, "speed": 0.5},
    {"alt": 45.0, "az": 90.0, "speed": 0.8},
    {"alt": 60.0, "az": 90.0, "speed": 0.3},
    {"alt": 60.0, "az": 180.0, "speed": 1.0},
    {"alt": 30.0, "az": 270.0, "speed": 0.5},
]


def make_idle_state(
    alt: float = 0.0, az: float = 0.0
) -> TelescopeState:
    return TelescopeState(
        current_alt_deg=alt,
        current_az_deg=az,
        status=StatusCode.IDLE,
    )


def make_moving_state(
    current_alt: float = 0.0,
    current_az: float = 0.0,
    target_alt: float = 45.0,
    target_az: float = 90.0,
) -> TelescopeState:
    return TelescopeState(
        current_alt_deg=current_alt,
        current_az_deg=current_az,
        status=StatusCode.MOVING,
        target_alt_deg=target_alt,
        target_az_deg=target_az,
    )


def make_error_state(
    error_codes: list = None,
) -> TelescopeState:
    if error_codes is None:
        error_codes = [10]  # MOTOR_STALL
    return TelescopeState(
        current_alt_deg=0.0,
        current_az_deg=0.0,
        status=StatusCode.ERROR,
        error_codes=error_codes,
    )
