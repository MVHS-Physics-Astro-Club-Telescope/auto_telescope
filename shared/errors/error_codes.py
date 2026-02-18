from enum import IntEnum
from typing import Dict


class ErrorCode(IntEnum):
    # Motor errors (10-19)
    MOTOR_STALL = 10
    MOTOR_OVERCURRENT = 11
    MOTOR_TIMEOUT = 12
    MOTOR_NOT_INITIALIZED = 13

    # Position errors (20-29)
    POSITION_OUT_OF_RANGE = 20
    POSITION_LIMIT_HIT = 21
    POSITION_UNKNOWN = 22

    # Focus errors (30-39)
    FOCUS_STALL = 30
    FOCUS_LIMIT_HIT = 31
    FOCUS_TIMEOUT = 32

    # Communication errors (40-49)
    COMMS_TIMEOUT = 40
    COMMS_DISCONNECT = 41
    COMMS_INVALID_MESSAGE = 42
    COMMS_PROTOCOL_ERROR = 43

    # Camera errors (50-59)
    CAMERA_DISCONNECT = 50
    CAMERA_CAPTURE_FAILED = 51
    CAMERA_TIMEOUT = 52

    # Sensor errors (60-69)
    SENSOR_READ_FAILED = 60
    SENSOR_OUT_OF_RANGE = 61

    # Safety errors (70-79)
    SAFETY_LIMIT_EXCEEDED = 70
    SAFETY_EMERGENCY_STOP = 71
    SAFETY_WATCHDOG_TIMEOUT = 72


ERROR_DESCRIPTIONS: Dict[int, str] = {
    ErrorCode.MOTOR_STALL: "Motor stalled during movement",
    ErrorCode.MOTOR_OVERCURRENT: "Motor drawing excessive current",
    ErrorCode.MOTOR_TIMEOUT: "Motor operation timed out",
    ErrorCode.MOTOR_NOT_INITIALIZED: "Motor not initialized before use",
    ErrorCode.POSITION_OUT_OF_RANGE: "Requested position outside valid range",
    ErrorCode.POSITION_LIMIT_HIT: "Physical position limit reached",
    ErrorCode.POSITION_UNKNOWN: "Current position is unknown",
    ErrorCode.FOCUS_STALL: "Focus motor stalled",
    ErrorCode.FOCUS_LIMIT_HIT: "Focus limit reached",
    ErrorCode.FOCUS_TIMEOUT: "Focus operation timed out",
    ErrorCode.COMMS_TIMEOUT: "Communication timed out",
    ErrorCode.COMMS_DISCONNECT: "Connection lost",
    ErrorCode.COMMS_INVALID_MESSAGE: "Received invalid message",
    ErrorCode.COMMS_PROTOCOL_ERROR: "Protocol framing error",
    ErrorCode.CAMERA_DISCONNECT: "Camera disconnected",
    ErrorCode.CAMERA_CAPTURE_FAILED: "Image capture failed",
    ErrorCode.CAMERA_TIMEOUT: "Camera operation timed out",
    ErrorCode.SENSOR_READ_FAILED: "Sensor read failed",
    ErrorCode.SENSOR_OUT_OF_RANGE: "Sensor value out of expected range",
    ErrorCode.SAFETY_LIMIT_EXCEEDED: "Safety limit exceeded",
    ErrorCode.SAFETY_EMERGENCY_STOP: "Emergency stop triggered",
    ErrorCode.SAFETY_WATCHDOG_TIMEOUT: "Safety watchdog timed out",
}


def get_error_description(code: int) -> str:
    return ERROR_DESCRIPTIONS.get(code, f"Unknown error code: {code}")
