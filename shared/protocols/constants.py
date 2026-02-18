# Network
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5050
CONNECT_TIMEOUT_S = 10.0
RECV_TIMEOUT_S = 5.0

# Framing: 4-byte big-endian length prefix
HEADER_SIZE = 4
MAX_MESSAGE_SIZE = 65536  # 64 KB

# Validation ranges — Alt/Az mount
ALT_MIN_DEG = 0.0
ALT_MAX_DEG = 90.0
AZ_MIN_DEG = 0.0
AZ_MAX_DEG = 360.0
SPEED_MIN = 0.0
SPEED_MAX = 1.0

# Focus
FOCUS_STEPS_MIN = 1
FOCUS_STEPS_MAX = 10000

# Safety (per CLAUDE.md: max 30s default timeout for motor commands)
DEFAULT_COMMAND_TIMEOUT_S = 30.0
