# Motor parameters — derivation
MOTOR_STEPS_PER_REV = 200
BELT_RATIO = 10.0
MICROSTEP_FACTOR = 16
STEPS_PER_DEGREE_ALT = MOTOR_STEPS_PER_REV * BELT_RATIO * MICROSTEP_FACTOR / 360.0  # ~88.9
STEPS_PER_DEGREE_AZ = MOTOR_STEPS_PER_REV * BELT_RATIO * MICROSTEP_FACTOR / 360.0   # ~88.9
MAX_STEP_RATE_HZ = 1000
MIN_STEP_RATE_HZ = 10
# TODO: ACCEL_STEPS_PER_S2 is defined but not yet used in the motion planner;
# implement acceleration ramp in MotorController.step() when hardware is ready.
ACCEL_STEPS_PER_S2 = 500

# Control loop
MAIN_LOOP_HZ = 50
STATE_REPORT_HZ = 5
WATCHDOG_TIMEOUT_S = 5.0

# Mechanical limits (wider than shared/ protocol limits for homing)
ALT_MIN_DEG = -5.0
ALT_MAX_DEG = 95.0
AZ_MIN_DEG = -5.0
AZ_MAX_DEG = 365.0

# Focus
FOCUS_POSITION_MIN = 0
FOCUS_POSITION_MAX = 10000
FOCUS_STEPS_PER_DEGREE = 100.0

# Reconnection
RECONNECT_DELAY_S = 2.0
MAX_RECONNECT_ATTEMPTS = 10

# Stepping
STEP_CHUNK_SIZE = 50
