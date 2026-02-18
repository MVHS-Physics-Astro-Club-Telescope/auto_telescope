import dataclasses
import time
from typing import Optional

from shared.enums.status_codes import StatusCode


@dataclasses.dataclass
class CameraState:
    is_connected: bool = False
    status: str = StatusCode.IDLE  # StatusCode value
    exposure_ms: Optional[float] = None
    gain: Optional[float] = None
    temperature_c: Optional[float] = None
    timestamp: float = dataclasses.field(default_factory=time.time, init=False)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CameraState":
        state = cls(
            is_connected=bool(data.get("is_connected", False)),
            status=str(data.get("status", StatusCode.IDLE)),
            exposure_ms=float(data["exposure_ms"]) if data.get("exposure_ms") is not None else None,
            gain=float(data["gain"]) if data.get("gain") is not None else None,
            temperature_c=float(data["temperature_c"]) if data.get("temperature_c") is not None else None,
        )
        if "timestamp" in data:
            state.timestamp = float(data["timestamp"])
        return state
