import abc
import threading
import time
from typing import List, Optional, Tuple

from pi.config.pins import MotorPins
from pi.hardware.gpio_setup import GPIOProvider, HIGH, LOW
from pi.utils.logger import get_logger
from pi.utils.timer import Timeout

logger = get_logger("motor_driver")

DIRECTION_FORWARD = 1
DIRECTION_REVERSE = 0


class MotorDriver(abc.ABC):
    @abc.abstractmethod
    def enable(self) -> None:
        ...

    @abc.abstractmethod
    def disable(self) -> None:
        ...

    @abc.abstractmethod
    def step(
        self,
        direction: int,
        num_steps: int,
        rate_hz: float,
        timeout_s: float = 30.0,
        stop_event: Optional[threading.Event] = None,
    ) -> int:
        ...

    @abc.abstractmethod
    def stop(self) -> None:
        ...

    @abc.abstractmethod
    def is_fault(self) -> bool:
        ...


class StepperMotorDriver(MotorDriver):
    def __init__(self, gpio: GPIOProvider, pins: MotorPins) -> None:
        self._gpio = gpio
        self._pins = pins
        self._enabled = False

    def enable(self) -> None:
        self._gpio.write(self._pins.enable, HIGH)
        self._enabled = True

    def disable(self) -> None:
        self._gpio.write(self._pins.enable, LOW)
        self._enabled = False

    def step(
        self,
        direction: int,
        num_steps: int,
        rate_hz: float,
        timeout_s: float = 30.0,
        stop_event: Optional[threading.Event] = None,
    ) -> int:
        if not self._enabled:
            self.enable()

        self._gpio.write(self._pins.direction, direction)
        period = 1.0 / rate_hz
        half_period = period / 2.0
        timeout = Timeout(timeout_s)
        steps_done = 0

        for _ in range(num_steps):
            if timeout.is_expired():
                logger.warning("Step timeout after %d/%d steps", steps_done, num_steps)
                break
            if stop_event is not None and stop_event.is_set():
                break

            self._gpio.write(self._pins.step, HIGH)
            time.sleep(half_period)
            self._gpio.write(self._pins.step, LOW)
            time.sleep(half_period)
            steps_done += 1

        return steps_done

    def stop(self) -> None:
        self._gpio.write(self._pins.step, LOW)

    def is_fault(self) -> bool:
        if self._pins.fault is None:
            return False
        return self._gpio.read(self._pins.fault) == LOW


class MockMotorDriver(MotorDriver):
    def __init__(self) -> None:
        self._enabled = False
        self._cumulative_steps = 0
        self._last_direction: Optional[int] = None
        self._calls: List[Tuple[int, int, float]] = []
        self._fault = False

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def step(
        self,
        direction: int,
        num_steps: int,
        rate_hz: float,
        timeout_s: float = 30.0,
        stop_event: Optional[threading.Event] = None,
    ) -> int:
        self._calls.append((direction, num_steps, rate_hz))
        self._last_direction = direction
        self._cumulative_steps += num_steps
        return num_steps

    def stop(self) -> None:
        pass

    def is_fault(self) -> bool:
        return self._fault

    def set_fault(self, fault: bool) -> None:
        self._fault = fault

    @property
    def cumulative_steps(self) -> int:
        return self._cumulative_steps

    @property
    def calls(self) -> List[Tuple[int, int, float]]:
        return self._calls
