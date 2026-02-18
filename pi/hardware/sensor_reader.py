import abc
import dataclasses
from typing import Optional

from pi.config.pins import SensorPins
from pi.hardware.gpio_setup import GPIOProvider, LOW
from pi.utils.logger import get_logger

logger = get_logger("sensors")


@dataclasses.dataclass
class LimitSwitchState:
    alt_low: bool = False
    alt_high: bool = False
    az_low: bool = False
    az_high: bool = False

    @property
    def any_hit(self) -> bool:
        return self.alt_low or self.alt_high or self.az_low or self.az_high


@dataclasses.dataclass
class EncoderReading:
    alt_counts: Optional[int] = None
    az_counts: Optional[int] = None


class SensorReader(abc.ABC):
    @abc.abstractmethod
    def read_limit_switches(self) -> LimitSwitchState:
        ...

    @abc.abstractmethod
    def read_encoders(self) -> EncoderReading:
        ...


class GPIOSensorReader(SensorReader):
    def __init__(self, gpio: GPIOProvider, pins: SensorPins) -> None:
        self._gpio = gpio
        self._pins = pins

    def read_limit_switches(self) -> LimitSwitchState:
        return LimitSwitchState(
            alt_low=self._gpio.read(self._pins.alt_limit_low) == LOW,
            alt_high=self._gpio.read(self._pins.alt_limit_high) == LOW,
            az_low=self._gpio.read(self._pins.az_limit_low) == LOW,
            az_high=self._gpio.read(self._pins.az_limit_high) == LOW,
        )

    def read_encoders(self) -> EncoderReading:
        return EncoderReading()


class MockSensorReader(SensorReader):
    def __init__(self) -> None:
        self._limits = LimitSwitchState()
        self._encoders = EncoderReading()

    def read_limit_switches(self) -> LimitSwitchState:
        return self._limits

    def read_encoders(self) -> EncoderReading:
        return self._encoders

    def set_limits(
        self,
        alt_low: bool = False,
        alt_high: bool = False,
        az_low: bool = False,
        az_high: bool = False,
    ) -> None:
        self._limits = LimitSwitchState(
            alt_low=alt_low, alt_high=alt_high,
            az_low=az_low, az_high=az_high,
        )

    def set_encoders(
        self,
        alt_counts: Optional[int] = None,
        az_counts: Optional[int] = None,
    ) -> None:
        self._encoders = EncoderReading(
            alt_counts=alt_counts, az_counts=az_counts,
        )
