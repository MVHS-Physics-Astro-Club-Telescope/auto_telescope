import argparse
import queue
import signal
import sys
import time
from typing import Optional

from shared.commands.move_command import MoveCommand
from shared.commands.focus_command import FocusCommand
from shared.commands.stop_command import StopCommand
from shared.protocols.constants import DEFAULT_HOST, DEFAULT_PORT
from pi.comms.message_parser import (
    build_ack_response,
    build_error_response,
    build_state_response,
    is_status_request,
    parse_command,
)
from pi.comms.tcp_client import TCPClient
from pi.comms.validator import is_valid_command
from pi.config.constants import MAIN_LOOP_HZ, STATE_REPORT_HZ
from pi.config.pins import ALT_MOTOR, AZ_MOTOR, FOCUS_MOTOR, SENSORS
from pi.control.focus_controller import FocusController
from pi.control.motor_controller import MotorController
from pi.control.safety_manager import SafetyManager
from pi.hardware.gpio_setup import (
    GPIOProvider,
    HardwareGPIOProvider,
    MockGPIOProvider,
    cleanup_gpio,
    initialize_gpio,
)
from pi.hardware.motor_driver import (
    MockMotorDriver,
    MotorDriver,
    StepperMotorDriver,
)
from pi.hardware.sensor_reader import (
    GPIOSensorReader,
    MockSensorReader,
    SensorReader,
)
from pi.state.error_state import ErrorState
from pi.state.telescope_state import TelescopeStateManager
from pi.utils.logger import get_logger
from pi.utils.timer import LoopTimer

logger = get_logger("main")

_shutdown = False


def _signal_handler(signum: int, frame: object) -> None:
    global _shutdown
    logger.info("Received signal %d, shutting down", signum)
    _shutdown = True


def create_hardware(use_mock: bool) -> tuple:
    if use_mock:
        gpio: GPIOProvider = MockGPIOProvider()
        alt_motor: MotorDriver = MockMotorDriver()
        az_motor: MotorDriver = MockMotorDriver()
        focus_motor: MotorDriver = MockMotorDriver()
        sensor_reader: SensorReader = MockSensorReader()
    else:
        gpio = HardwareGPIOProvider()
        initialize_gpio(gpio, [ALT_MOTOR, AZ_MOTOR, FOCUS_MOTOR], SENSORS)
        alt_motor = StepperMotorDriver(gpio, ALT_MOTOR)
        az_motor = StepperMotorDriver(gpio, AZ_MOTOR)
        focus_motor = StepperMotorDriver(gpio, FOCUS_MOTOR)
        sensor_reader = GPIOSensorReader(gpio, SENSORS)

    return gpio, alt_motor, az_motor, focus_motor, sensor_reader


def main_loop(
    tcp: TCPClient,
    msg_queue: "queue.Queue[dict]",
    motor_ctrl: MotorController,
    focus_ctrl: FocusController,
    safety: SafetyManager,
    state_mgr: TelescopeStateManager,
) -> None:
    global _shutdown
    loop_timer = LoopTimer(MAIN_LOOP_HZ)
    report_interval = 1.0 / STATE_REPORT_HZ
    last_report = 0.0

    while not _shutdown:
        safety.feed_watchdog()
        safety.check()

        # Process incoming messages (non-blocking)
        try:
            data = msg_queue.get_nowait()
        except queue.Empty:
            data = None

        if data is not None:
            _dispatch_command(
                data, tcp, motor_ctrl, focus_ctrl, state_mgr,
            )

        # Periodic state report
        now = time.monotonic()
        if now - last_report >= report_interval:
            snapshot = state_mgr.get_snapshot()
            tcp.send(build_state_response(snapshot))
            last_report = now

        loop_timer.tick()


def _dispatch_command(
    data: dict,
    tcp: TCPClient,
    motor_ctrl: MotorController,
    focus_ctrl: FocusController,
    state_mgr: TelescopeStateManager,
) -> None:
    if is_status_request(data):
        snapshot = state_mgr.get_snapshot()
        tcp.send(build_state_response(snapshot))
        return

    if not is_valid_command(data):
        cmd_id = data.get("command_id", "unknown")
        tcp.send(build_error_response(cmd_id, "Invalid command"))
        return

    cmd = parse_command(data)
    if cmd is None:
        return

    tcp.send(build_ack_response(cmd.command_id))

    if isinstance(cmd, MoveCommand):
        motor_ctrl.execute_move(cmd)
    elif isinstance(cmd, FocusCommand):
        focus_ctrl.execute_focus(cmd)
    elif isinstance(cmd, StopCommand):
        motor_ctrl.execute_stop(cmd)


def run(host: str, port: int, use_mock: bool) -> None:
    global _shutdown
    _shutdown = False

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    gpio, alt_motor, az_motor, focus_motor, sensor_reader = create_hardware(use_mock)

    try:
        error_state = ErrorState()
        state_mgr = TelescopeStateManager(error_state)
        motors = [alt_motor, az_motor, focus_motor]
        safety = SafetyManager(sensor_reader, state_mgr, error_state, motors)
        motor_ctrl = MotorController(alt_motor, az_motor, safety, state_mgr, error_state)
        focus_ctrl = FocusController(focus_motor, safety, state_mgr, error_state)

        tcp = TCPClient(host, port, error_state)
        msg_queue: queue.Queue[dict] = queue.Queue()

        logger.info("Connecting to host %s:%d (mock=%s)", host, port, use_mock)
        if tcp.connect():
            tcp.start_receiver(msg_queue)
            logger.info("Entering main loop at %d Hz", MAIN_LOOP_HZ)
            main_loop(tcp, msg_queue, motor_ctrl, focus_ctrl, safety, state_mgr)
        else:
            logger.error("Failed to connect to host")

        tcp.disconnect()
    finally:
        cleanup_gpio(gpio)
        logger.info("Shutdown complete")


def main() -> None:
    parser = argparse.ArgumentParser(description="Telescope Pi Controller")
    parser.add_argument("--host", default="127.0.0.1", help="Host IP address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Host port")
    parser.add_argument("--mock", action="store_true", help="Use mock hardware")
    args = parser.parse_args()
    run(args.host, args.port, args.mock)


if __name__ == "__main__":
    main()
