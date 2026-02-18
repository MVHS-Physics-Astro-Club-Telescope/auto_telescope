import dataclasses
import time
import uuid
from typing import Optional

from shared.enums.command_types import CommandType


@dataclasses.dataclass
class StopCommand:
    emergency: bool = False
    reason: str = ""
    command_id: Optional[str] = None
    command_type: str = dataclasses.field(default=CommandType.STOP, init=False)
    timestamp: float = dataclasses.field(default_factory=time.time, init=False)

    def __post_init__(self):
        if self.command_id is None:
            self.command_id = str(uuid.uuid4())

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StopCommand":
        cmd = cls(
            emergency=bool(data.get("emergency", False)),
            reason=str(data.get("reason", "")),
            command_id=data.get("command_id"),
        )
        if "timestamp" in data:
            cmd.timestamp = float(data["timestamp"])
        return cmd
