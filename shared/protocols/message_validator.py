from typing import List

from shared.enums.command_types import CommandType
from shared.protocols.constants import (
    ALT_MAX_DEG,
    ALT_MIN_DEG,
    AZ_MAX_DEG,
    AZ_MIN_DEG,
    FOCUS_STEPS_MAX,
    FOCUS_STEPS_MIN,
    SPEED_MAX,
    SPEED_MIN,
)


class ValidationError(Exception):
    pass


def validate_move_command(data: dict) -> List[str]:
    errors: List[str] = []

    if "target_alt_deg" not in data:
        errors.append("Missing required field: target_alt_deg")
    else:
        alt = data["target_alt_deg"]
        try:
            alt = float(alt)
            if alt < ALT_MIN_DEG or alt > ALT_MAX_DEG:
                errors.append(f"target_alt_deg {alt} outside range [{ALT_MIN_DEG}, {ALT_MAX_DEG}]")
        except (TypeError, ValueError):
            errors.append(f"target_alt_deg must be numeric, got {type(alt).__name__}")

    if "target_az_deg" not in data:
        errors.append("Missing required field: target_az_deg")
    else:
        az = data["target_az_deg"]
        try:
            az = float(az)
            if az < AZ_MIN_DEG or az > AZ_MAX_DEG:
                errors.append(f"target_az_deg {az} outside range [{AZ_MIN_DEG}, {AZ_MAX_DEG}]")
        except (TypeError, ValueError):
            errors.append(f"target_az_deg must be numeric, got {type(az).__name__}")

    if "speed" in data:
        speed = data["speed"]
        try:
            speed = float(speed)
            if speed < SPEED_MIN or speed > SPEED_MAX:
                errors.append(f"speed {speed} outside range [{SPEED_MIN}, {SPEED_MAX}]")
        except (TypeError, ValueError):
            errors.append(f"speed must be numeric, got {type(speed).__name__}")

    return errors


def validate_focus_command(data: dict) -> List[str]:
    errors: List[str] = []

    if "direction" not in data:
        errors.append("Missing required field: direction")
    else:
        direction = data["direction"]
        if direction not in ("in", "out"):
            errors.append(f"direction must be 'in' or 'out', got '{direction}'")

    if "steps" not in data:
        errors.append("Missing required field: steps")
    else:
        steps = data["steps"]
        try:
            steps = int(steps)
            if steps < FOCUS_STEPS_MIN or steps > FOCUS_STEPS_MAX:
                errors.append(f"steps {steps} outside range [{FOCUS_STEPS_MIN}, {FOCUS_STEPS_MAX}]")
        except (TypeError, ValueError):
            errors.append(f"steps must be integer, got {type(steps).__name__}")

    return errors


def validate_stop_command(data: dict) -> List[str]:
    errors: List[str] = []

    if "emergency" in data and not isinstance(data["emergency"], bool):
        errors.append(f"emergency must be boolean, got {type(data['emergency']).__name__}")

    return errors


def validate_message(data: dict) -> List[str]:
    if not isinstance(data, dict):
        raise ValidationError(f"Message must be a dict, got {type(data).__name__}")

    if "command_type" not in data:
        raise ValidationError("Message missing required field: command_type")

    command_type = data["command_type"]

    try:
        ct = CommandType(command_type)
    except ValueError:
        raise ValidationError(f"Unknown command_type: {command_type}")

    if ct == CommandType.MOVE:
        return validate_move_command(data)
    elif ct == CommandType.FOCUS:
        return validate_focus_command(data)
    elif ct == CommandType.STOP:
        return validate_stop_command(data)
    elif ct == CommandType.STATUS_REQUEST:
        return []

    return []
