from enum import Enum


class StatusCode(str, Enum):
    OK = "ok"
    BUSY = "busy"
    ERROR = "error"
    MOVING = "moving"
    FOCUSING = "focusing"
    IDLE = "idle"
    EMERGENCY_STOP = "emergency_stop"
