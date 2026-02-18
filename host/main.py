import argparse
import queue
import signal
import socket
import sys
import threading
import time
from typing import Optional

from shared.protocols.constants import DEFAULT_PORT, RECV_TIMEOUT_S
from host.comms.receiver import Receiver
from host.comms.sender import Sender
from host.config.constants import (
    DEFAULT_OBSERVER_ELEV,
    DEFAULT_OBSERVER_LAT,
    DEFAULT_OBSERVER_LON,
    SERVER_HOST,
    TRACKING_LOOP_HZ,
)
from host.control.focus_controller import FocusController
from host.control.tracking_controller import TrackingController
from host.state.session_logs import SessionLog
from host.state.telescope_state import HostTelescopeState
from host.ui.host_interface import HostInterface
from host.utils.logger import get_logger

logger = get_logger("main")

_shutdown = False


def _signal_handler(signum: int, frame: object) -> None:
    global _shutdown
    logger.info("Received signal %d, shutting down", signum)
    _shutdown = True


def start_tcp_server(host: str, port: int) -> socket.socket:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
    server.settimeout(1.0)
    logger.info("TCP server listening on %s:%d", host, port)
    return server


def wait_for_pi(server: socket.socket) -> Optional[socket.socket]:
    global _shutdown
    logger.info("Waiting for Pi to connect...")
    while not _shutdown:
        try:
            client_sock, addr = server.accept()
            client_sock.settimeout(RECV_TIMEOUT_S)
            logger.info("Pi connected from %s:%d", addr[0], addr[1])
            return client_sock
        except socket.timeout:
            continue
        except OSError as e:
            if not _shutdown:
                logger.error("Accept error: %s", e)
            break
    return None


def tracking_loop(
    tracking: TrackingController,
    stop_event: threading.Event,
) -> None:
    interval = 1.0 / TRACKING_LOOP_HZ
    while not stop_event.is_set():
        start = time.monotonic()
        try:
            tracking.update()
        except Exception as e:
            logger.error("Tracking update error: %s", e)
        elapsed = time.monotonic() - start
        sleep_time = interval - elapsed
        if sleep_time > 0:
            stop_event.wait(timeout=sleep_time)


def run(
    host: str,
    port: int,
    lat: float,
    lon: float,
    elev: float,
    simulate: bool = False,
) -> None:
    global _shutdown
    _shutdown = False

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Shared state
    telescope_state = HostTelescopeState()
    session_log = SessionLog()
    response_queue: queue.Queue[dict] = queue.Queue()

    # Comms
    sender = Sender(session_log, response_queue)
    receiver = Receiver(telescope_state, session_log, response_queue)

    # Control
    tracking = TrackingController(
        sender, telescope_state, session_log, lat, lon, elev,
    )
    focus = FocusController(sender, telescope_state, session_log)

    # UI
    interface = HostInterface(
        sender, tracking, focus, telescope_state, session_log,
    )

    if simulate:
        _run_simulated(
            sender, receiver, tracking, focus,
            telescope_state, session_log, interface,
        )
        return

    # Real TCP mode
    server = start_tcp_server(host, port)
    try:
        client_sock = wait_for_pi(server)
        if client_sock is None:
            logger.error("No Pi connection, exiting")
            return

        sender.set_socket(client_sock)
        receiver.start(client_sock)

        # Start tracking background thread
        track_stop = threading.Event()
        track_thread = threading.Thread(
            target=tracking_loop,
            args=(tracking, track_stop),
            name="tracking-loop",
            daemon=True,
        )
        track_thread.start()

        try:
            interface.run()
        finally:
            _shutdown = True
            track_stop.set()
            tracking.stop_tracking()
            receiver.stop()
            track_thread.join(timeout=2.0)
            client_sock.close()
    finally:
        server.close()
        logger.info("Shutdown complete")


def _run_simulated(
    sender, receiver, tracking, focus,
    telescope_state, session_log, interface,
) -> None:
    from host.simulation.simulator import TelescopeSimulator

    logger.info("Running in simulation mode")
    sim = TelescopeSimulator()

    # Override sender to route through simulator
    class SimSender:
        def __init__(self, real_sender, simulator, ts):
            self._real = real_sender
            self._sim = simulator
            self._ts = ts

        def send_move(self, alt, az, speed=0.5):
            from shared.commands.move_command import MoveCommand
            cmd = MoveCommand(target_alt_deg=alt, target_az_deg=az, speed=speed)
            resp = self._sim.send_command(cmd.to_dict())
            state = self._sim.get_state()
            self._ts.update_from_pi(state)
            return cmd.command_id

        def send_focus(self, direction, steps):
            from shared.commands.focus_command import FocusCommand
            cmd = FocusCommand(direction=direction, steps=steps)
            self._sim.send_command(cmd.to_dict())
            state = self._sim.get_state()
            self._ts.update_from_pi(state)
            return cmd.command_id

        def send_stop(self, emergency=False):
            from shared.commands.stop_command import StopCommand
            cmd = StopCommand(emergency=emergency)
            self._sim.send_command(cmd.to_dict())
            state = self._sim.get_state()
            self._ts.update_from_pi(state)
            return cmd.command_id

        def send_status_request(self):
            resp = self._sim.send_command(
                {"command_type": "status_request"}
            )
            return True

    sim_sender = SimSender(sender, sim, telescope_state)

    # Inject the sim sender into tracking and focus
    tracking._sender = sim_sender
    focus._sender = sim_sender

    interface._sender = sim_sender
    interface.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Telescope Host Controller")
    parser.add_argument("--host", default=SERVER_HOST, help="Bind address")
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="Listen port"
    )
    parser.add_argument(
        "--lat", type=float, default=DEFAULT_OBSERVER_LAT,
        help="Observer latitude (deg)",
    )
    parser.add_argument(
        "--lon", type=float, default=DEFAULT_OBSERVER_LON,
        help="Observer longitude (deg)",
    )
    parser.add_argument(
        "--elev", type=float, default=DEFAULT_OBSERVER_ELEV,
        help="Observer elevation (m)",
    )
    parser.add_argument(
        "--simulate", action="store_true",
        help="Run in simulation mode without Pi",
    )
    args = parser.parse_args()
    run(args.host, args.port, args.lat, args.lon, args.elev, args.simulate)


if __name__ == "__main__":
    main()
