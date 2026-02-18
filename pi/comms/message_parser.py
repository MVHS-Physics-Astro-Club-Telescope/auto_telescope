import time
from typing import Optional, Union

from shared.commands.focus_command import FocusCommand
from shared.commands.move_command import MoveCommand
from shared.commands.stop_command import StopCommand
from shared.enums.command_types import CommandType
from shared.state.telescope_state import TelescopeState
from pi.utils.logger import get_logger

logger = get_logger("parser")

Command = Union[MoveCommand, FocusCommand, StopCommand]


def parse_command(data: dict) -> Optional[Command]:
    command_type = data.get("command_type")

    if command_type == CommandType.MOVE:
        return MoveCommand.from_dict(data)
    elif command_type == CommandType.FOCUS:
        return FocusCommand.from_dict(data)
    elif command_type == CommandType.STOP:
        return StopCommand.from_dict(data)

    logger.warning("Unknown command type: %s", command_type)
    return None


def is_status_request(data: dict) -> bool:
    return data.get("command_type") == CommandType.STATUS_REQUEST


def build_state_response(state: TelescopeState) -> dict:
    response = state.to_dict()
    response["message_type"] = "state_report"
    return response


def build_ack_response(command_id: str) -> dict:
    return {
        "message_type": "ack",
        "command_id": command_id,
        "timestamp": time.time(),
    }


def build_error_response(command_id: str, error_msg: str) -> dict:
    return {
        "message_type": "error",
        "command_id": command_id,
        "error": error_msg,
        "timestamp": time.time(),
    }
