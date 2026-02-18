import abc
from typing import Dict, List

from pi.config.pins import MotorPins, SensorPins
from pi.utils.logger import get_logger

logger = get_logger("gpio")

OUTPUT = "output"
INPUT = "input"
HIGH = 1
LOW = 0


class GPIOProvider(abc.ABC):
    @abc.abstractmethod
    def setup_output(self, pin: int) -> None:
        ...

    @abc.abstractmethod
    def setup_input(self, pin: int, pull_up: bool = False) -> None:
        ...

    @abc.abstractmethod
    def write(self, pin: int, value: int) -> None:
        ...

    @abc.abstractmethod
    def read(self, pin: int) -> int:
        ...

    @abc.abstractmethod
    def cleanup(self) -> None:
        ...


class MockGPIOProvider(GPIOProvider):
    def __init__(self) -> None:
        self._pins: Dict[int, int] = {}
        self._modes: Dict[int, str] = {}

    def setup_output(self, pin: int) -> None:
        self._modes[pin] = OUTPUT
        self._pins[pin] = LOW

    def setup_input(self, pin: int, pull_up: bool = False) -> None:
        self._modes[pin] = INPUT
        self._pins[pin] = HIGH if pull_up else LOW

    def write(self, pin: int, value: int) -> None:
        self._pins[pin] = value

    def read(self, pin: int) -> int:
        return self._pins.get(pin, LOW)

    def cleanup(self) -> None:
        self._pins.clear()
        self._modes.clear()


class HardwareGPIOProvider(GPIOProvider):
    def __init__(self) -> None:
        try:
            import RPi.GPIO as GPIO  # type: ignore[import-untyped]
            self._gpio = GPIO
            self._gpio.setmode(GPIO.BCM)
            self._gpio.setwarnings(False)
        except ImportError:
            raise RuntimeError(
                "RPi.GPIO not available — use MockGPIOProvider for testing"
            )

    def setup_output(self, pin: int) -> None:
        self._gpio.setup(pin, self._gpio.OUT, initial=self._gpio.LOW)

    def setup_input(self, pin: int, pull_up: bool = False) -> None:
        pud = self._gpio.PUD_UP if pull_up else self._gpio.PUD_DOWN
        self._gpio.setup(pin, self._gpio.IN, pull_up_down=pud)

    def write(self, pin: int, value: int) -> None:
        self._gpio.output(pin, value)

    def read(self, pin: int) -> int:
        return self._gpio.input(pin)

    def cleanup(self) -> None:
        self._gpio.cleanup()


def initialize_gpio(
    gpio: GPIOProvider, motor_pins_list: List[MotorPins], sensor_pins: SensorPins
) -> None:
    for mp in motor_pins_list:
        gpio.setup_output(mp.step)
        gpio.setup_output(mp.direction)
        gpio.setup_output(mp.enable)
        if mp.fault is not None:
            gpio.setup_input(mp.fault, pull_up=True)

    for pin in [
        sensor_pins.alt_limit_low,
        sensor_pins.alt_limit_high,
        sensor_pins.az_limit_low,
        sensor_pins.az_limit_high,
    ]:
        gpio.setup_input(pin, pull_up=True)

    logger.info("GPIO initialized: %d motors, sensors ready", len(motor_pins_list))


def cleanup_gpio(gpio: GPIOProvider) -> None:
    gpio.cleanup()
    logger.info("GPIO cleaned up")
