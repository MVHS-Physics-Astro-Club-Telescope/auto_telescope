import dataclasses
import time
from typing import List, Optional

from shared.enums.status_codes import StatusCode


@dataclasses.dataclass
class TelescopeState:
    current_alt_deg: float
    current_az_deg: float
    status: str  # StatusCode value
    target_alt_deg: Optional[float] = None
    target_az_deg: Optional[float] = None
    error_codes: List[int] = dataclasses.field(default_factory=list)
    focus_position: Optional[int] = None
    is_tracking: bool = False
    timestamp: float = dataclasses.field(default_factory=time.time, init=False)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TelescopeState":
        state = cls(
            current_alt_deg=float(data["current_alt_deg"]),
            current_az_deg=float(data["current_az_deg"]),
            status=str(data["status"]),
            target_alt_deg=float(data["target_alt_deg"]) if data.get("target_alt_deg") is not None else None,
            target_az_deg=float(data["target_az_deg"]) if data.get("target_az_deg") is not None else None,
            error_codes=[int(c) for c in data.get("error_codes", [])],
            focus_position=int(data["focus_position"]) if data.get("focus_position") is not None else None,
            is_tracking=bool(data.get("is_tracking", False)),
        )
        if "timestamp" in data:
            state.timestamp = float(data["timestamp"])
        return state
