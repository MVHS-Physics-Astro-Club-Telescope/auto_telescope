import dataclasses
import time
import uuid
from typing import Optional

from shared.enums.command_types import CommandType
from shared.protocols.constants import DEFAULT_COMMAND_TIMEOUT_S


@dataclasses.dataclass
class MoveCommand:
    target_alt_deg: float
    target_az_deg: float
    speed: float = 0.5
    timeout_s: float = DEFAULT_COMMAND_TIMEOUT_S
    command_id: Optional[str] = None
    command_type: str = dataclasses.field(default=CommandType.MOVE, init=False)
    timestamp: float = dataclasses.field(default_factory=time.time, init=False)

    def __post_init__(self):
        if self.command_id is None:
            self.command_id = str(uuid.uuid4())

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MoveCommand":
        cmd = cls(
            target_alt_deg=float(data["target_alt_deg"]),
            target_az_deg=float(data["target_az_deg"]),
            speed=float(data.get("speed", 0.5)),
            timeout_s=float(data.get("timeout_s", DEFAULT_COMMAND_TIMEOUT_S)),
            command_id=data.get("command_id"),
        )
        if "timestamp" in data:
            cmd.timestamp = float(data["timestamp"])
        return cmd
