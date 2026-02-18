from enum import Enum


class CommandType(str, Enum):
    MOVE = "move"
    FOCUS = "focus"
    STOP = "stop"
    STATUS_REQUEST = "status_request"
