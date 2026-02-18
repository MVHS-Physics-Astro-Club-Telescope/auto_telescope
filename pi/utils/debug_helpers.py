import os
from typing import Dict, Any


def format_state_summary(state_dict: Dict[str, Any]) -> str:
    alt = state_dict.get("current_alt_deg", "?")
    az = state_dict.get("current_az_deg", "?")
    status = state_dict.get("status", "?")
    errors = state_dict.get("error_codes", [])
    return f"alt={alt} az={az} status={status} errors={errors}"


def format_command_summary(cmd_dict: Dict[str, Any]) -> str:
    cmd_type = cmd_dict.get("command_type", "?")
    cmd_id = cmd_dict.get("command_id", "?")
    if cmd_type == "move":
        alt = cmd_dict.get("target_alt_deg", "?")
        az = cmd_dict.get("target_az_deg", "?")
        return f"MOVE alt={alt} az={az} id={cmd_id}"
    elif cmd_type == "focus":
        direction = cmd_dict.get("direction", "?")
        steps = cmd_dict.get("steps", "?")
        return f"FOCUS {direction} steps={steps} id={cmd_id}"
    elif cmd_type == "stop":
        emergency = cmd_dict.get("emergency", False)
        return f"STOP emergency={emergency} id={cmd_id}"
    return f"{cmd_type} id={cmd_id}"


def is_hardware_available() -> bool:
    try:
        with open("/proc/device-tree/model", "r") as f:
            model = f.read()
        return "Raspberry Pi" in model
    except (FileNotFoundError, PermissionError, OSError):
        return False
