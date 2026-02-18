from typing import Callable, Dict, Optional

from host.comms.sender import Sender
from host.config.constants import (
    PID_KP,
    PID_KI,
    PID_KD,
    TRACKING_TOLERANCE_DEG,
)
from host.control.error_correction import PIDController
from host.state.session_logs import SessionLog
from host.state.telescope_state import HostTelescopeState
from host.utils.logger import get_logger
from host.utils.math_utils import angular_distance, alt_az_delta

logger = get_logger("tracking")


class TrackingController:
    """Resolves celestial targets and drives the telescope to track them."""

    def __init__(
        self,
        sender: Sender,
        telescope_state: HostTelescopeState,
        session_log: SessionLog,
        lat: float,
        lon: float,
        elev: float,
        coordinate_resolver: Optional[Callable] = None,
    ) -> None:
        self._sender = sender
        self._state = telescope_state
        self._session_log = session_log
        self._lat = lat
        self._lon = lon
        self._elev = elev
        self._resolve = coordinate_resolver or self._default_resolver
        self._pid = PIDController(
            kp=PID_KP, ki=PID_KI, kd=PID_KD,
            output_min=0.05, output_max=1.0,
        )
        self._tracking = False
        self._target_name: Optional[str] = None
        self._target_alt: Optional[float] = None
        self._target_az: Optional[float] = None

    @staticmethod
    def _default_resolver(name: str, lat: float, lon: float, elev: float) -> tuple:
        from host.control.desired_position import get_object_coordinates
        return get_object_coordinates(name, lat, lon, elev)

    def start_tracking(self, target_name: str) -> bool:
        try:
            ra, dec, alt, az, visible = self._resolve(
                target_name, self._lat, self._lon, self._elev,
            )
        except (ValueError, Exception) as e:
            logger.error("Cannot resolve target '%s': %s", target_name, e)
            self._session_log.log_error(
                "Target resolution failed: %s" % e,
                {"target": target_name},
            )
            return False

        if not visible:
            logger.warning("Target '%s' is below the horizon (alt=%.2f)", target_name, alt)
            self._session_log.log_error(
                "Target below horizon",
                {"target": target_name, "alt": alt},
            )
            return False

        self._target_name = target_name
        self._target_alt = alt
        self._target_az = az
        self._tracking = True
        self._pid.reset()
        self._state.set_tracking_target(target_name)

        logger.info(
            "Tracking started: %s at alt=%.2f az=%.2f",
            target_name, alt, az,
        )
        self._session_log.log_command(
            "track_start",
            {"target": target_name, "alt": alt, "az": az},
        )
        return True

    def stop_tracking(self) -> None:
        if self._tracking:
            self._sender.send_stop(emergency=False)
        self._tracking = False
        self._target_name = None
        self._target_alt = None
        self._target_az = None
        self._pid.reset()
        self._state.clear_tracking_target()
        logger.info("Tracking stopped")

    @property
    def is_tracking(self) -> bool:
        return self._tracking

    def update(self) -> None:
        if not self._tracking or self._target_name is None:
            return

        # Re-resolve target position (sidereal motion)
        try:
            ra, dec, alt, az, visible = self._resolve(
                self._target_name, self._lat, self._lon, self._elev,
            )
        except Exception as e:
            logger.error("Re-resolve failed: %s", e)
            return

        if not visible:
            logger.warning("Target '%s' set below horizon, stopping", self._target_name)
            self.stop_tracking()
            return

        self._target_alt = alt
        self._target_az = az

        # Get current position from Pi
        pos = self._state.get_position()
        if pos is None:
            return
        cur_alt, cur_az = pos

        # Compute error
        distance = angular_distance(cur_alt, cur_az, alt, az)

        if distance < TRACKING_TOLERANCE_DEG:
            return

        speed = self._pid.compute(distance)
        d_alt, d_az = alt_az_delta(cur_alt, cur_az, alt, az)

        self._sender.send_move(alt, az, speed)

    def get_tracking_info(self) -> Dict:
        pos = self._state.get_position()
        cur_alt = pos[0] if pos else 0.0
        cur_az = pos[1] if pos else 0.0
        t_alt = self._target_alt if self._target_alt is not None else 0.0
        t_az = self._target_az if self._target_az is not None else 0.0

        distance = angular_distance(cur_alt, cur_az, t_alt, t_az) if self._tracking else 0.0

        return {
            "tracking": self._tracking,
            "target": self._target_name or "",
            "target_alt": t_alt,
            "target_az": t_az,
            "error_deg": distance,
            "within_tolerance": distance < TRACKING_TOLERANCE_DEG,
        }
