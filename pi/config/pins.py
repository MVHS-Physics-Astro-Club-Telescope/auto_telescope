import dataclasses
from typing import Optional


@dataclasses.dataclass(frozen=True)
class MotorPins:
    step: int
    direction: int
    enable: int
    fault: Optional[int] = None


@dataclasses.dataclass(frozen=True)
class SensorPins:
    alt_limit_low: int
    alt_limit_high: int
    az_limit_low: int
    az_limit_high: int
    alt_encoder_a: Optional[int] = None
    alt_encoder_b: Optional[int] = None
    az_encoder_a: Optional[int] = None
    az_encoder_b: Optional[int] = None


# BCM pin assignments (placeholders — update for actual wiring)
ALT_MOTOR = MotorPins(step=17, direction=27, enable=22, fault=5)
AZ_MOTOR = MotorPins(step=23, direction=24, enable=25, fault=6)
FOCUS_MOTOR = MotorPins(step=12, direction=16, enable=20, fault=None)

SENSORS = SensorPins(
    alt_limit_low=13,
    alt_limit_high=19,
    az_limit_low=26,
    az_limit_high=21,
)
