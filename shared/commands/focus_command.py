import dataclasses
import time
import uuid
from typing import Optional

from shared.enums.command_types import CommandType
from shared.protocols.constants import DEFAULT_COMMAND_TIMEOUT_S


FOCUS_IN = "in"
FOCUS_OUT = "out"


@dataclasses.dataclass
class FocusCommand:
    direction: str  # FOCUS_IN or FOCUS_OUT
    steps: int
    timeout_s: float = DEFAULT_COMMAND_TIMEOUT_S
    command_id: Optional[str] = None
    command_type: str = dataclasses.field(default=CommandType.FOCUS, init=False)
    timestamp: float = dataclasses.field(default_factory=time.time, init=False)

    def __post_init__(self):
        if self.command_id is None:
            self.command_id = str(uuid.uuid4())

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FocusCommand":
        cmd = cls(
            direction=str(data["direction"]),
            steps=int(data["steps"]),
            timeout_s=float(data.get("timeout_s", DEFAULT_COMMAND_TIMEOUT_S)),
            command_id=data.get("command_id"),
        )
        if "timestamp" in data:
            cmd.timestamp = float(data["timestamp"])
        return cmd
