# Architecture

## System Overview

The telescope software is a two-process system connected over TCP:

```
┌───────────────────────────────────────────────────────────────────┐
│                         Host Computer                             │
│                                                                   │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌───────────┐  │
│  │ CLI / UI │  │   Tracking   │  │  Autofocus  │  │ Celestial │  │
│  │          │  │  Controller  │  │ Controller  │  │ Resolver  │  │
│  └────┬─────┘  └──────┬───────┘  └─────┬──────┘  └─────┬─────┘  │
│       │               │                │               │         │
│       └───────────┬────┴────────────────┴───────────────┘         │
│                   │                                               │
│  ┌────────────────▼──────────────────┐  ┌──────────────────────┐ │
│  │  Sender (send_move/focus/stop)    │  │  HostTelescopeState  │ │
│  └────────────────┬──────────────────┘  └──────────▲───────────┘ │
│                   │                                │              │
│  ┌────────────────▼──────────────────────────────┐ │              │
│  │          TCP Server (port 5050)                │ │              │
│  │  ┌──────────────────────────────────────────┐ │ │              │
│  │  │ Receiver (background thread)             │─┼─┘              │
│  │  │  - state_report -> HostTelescopeState    │ │                │
│  │  │  - ack/error -> response_queue           │ │                │
│  │  └──────────────────────────────────────────┘ │                │
│  └───────────────────────────────────────────────┘                │
└───────────────────────────┬───────────────────────────────────────┘
                            │  TCP (4-byte length-prefixed JSON)
                            │
                  ┌─────────┴─────────┐
                  │  shared/ protocol  │
                  │  - MoveCommand     │
                  │  - FocusCommand    │
                  │  - StopCommand     │
                  │  - TelescopeState  │
                  │  - StatusCode      │
                  │  - ErrorCode       │
                  └─────────┬─────────┘
                            │
┌───────────────────────────▼───────────────────────────────────────┐
│                       Raspberry Pi                                │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │  TCPClient (connect, background receiver, send)           │    │
│  └───────────────────────┬───────────────────────────────────┘    │
│                          │                                        │
│  ┌───────────────────────▼───────────────────────────────────┐    │
│  │  Main Loop (50 Hz, single-threaded)                       │    │
│  │  - Pull from msg_queue                                    │    │
│  │  - _dispatch_command() -> ack + execute                   │    │
│  │  - Periodic state reports (5 Hz)                          │    │
│  │  - Safety checks every tick                               │    │
│  └──────┬─────────────────┬──────────────────┬───────────────┘    │
│         │                 │                  │                    │
│  ┌──────▼──────┐  ┌───────▼───────┐  ┌──────▼──────────┐        │
│  │   Motor     │  │    Focus      │  │  Safety         │        │
│  │  Controller │  │  Controller   │  │  Manager        │        │
│  │             │  │               │  │                  │        │
│  │ - alt axis  │  │ - position    │  │ - limit switches │        │
│  │ - az axis   │  │   tracking    │  │ - position bounds│        │
│  │ - chunked   │  │ - in/out      │  │ - watchdog       │        │
│  │   stepping  │  │               │  │ - emergency stop │        │
│  └──────┬──────┘  └───────┬───────┘  └──────┬──────────┘        │
│         │                 │                  │                    │
│  ┌──────▼─────────────────▼──────────────────▼───────────────┐    │
│  │  Hardware ABCs (MotorDriver, SensorReader, GPIOProvider)  │    │
│  │  - StepperMotorDriver / MockMotorDriver                   │    │
│  │  - GPIOSensorReader / MockSensorReader                    │    │
│  │  - HardwareGPIOProvider / MockGPIOProvider                │    │
│  └───────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────┘
```

## Layers

### shared/ -- Protocol Contract

The shared layer defines the communication contract consumed by both Host and Pi. Neither side imports the other; they only import shared.

**Commands** (Host -> Pi):
- `MoveCommand` -- target alt/az in degrees, speed (0-1), timeout
- `FocusCommand` -- direction (in/out), steps, timeout
- `StopCommand` -- emergency flag, reason string

**State** (Pi -> Host):
- `TelescopeState` -- current position, status, target, error codes, focus position, tracking flag

**Protocol**:
- TCP with 4-byte big-endian length prefix followed by UTF-8 JSON payload
- Max message size: 64 KB
- Message types: command (Host->Pi), ack/error/state_report (Pi->Host)
- `MessageValidator` enforces ranges (alt 0-90, az 0-360, speed 0-1, focus steps 1-10000)

**Enums**:
- `CommandType`: MOVE, FOCUS, STOP, STATUS_REQUEST
- `StatusCode`: IDLE, MOVING, FOCUSING, EMERGENCY_STOP, OK, BUSY, ERROR
- `ErrorCode`: Motor (10-19), Position (20-29), Focus (30-39), Comms (40-49), Camera (50-59), Sensor (60-69), Safety (70-79)

### host/ -- High-Level Control

The Host is hardware-agnostic. It never references GPIO pins, motor drivers, or Pi-specific values.

**Control flow**:
1. `main.py` starts a TCP server and waits for Pi to connect
2. Once connected, the CLI (`host_interface.py`) accepts user commands
3. Commands are validated (`validator.py`), serialized, and sent via `Sender`
4. `Receiver` runs a background thread processing incoming messages:
   - `state_report` -> updates `HostTelescopeState`
   - `ack` / `error` -> routes to `response_queue` for `Sender.wait_for_ack()`

**Tracking loop** (`tracking_controller.py`):
1. Resolve target name to RA/Dec via astropy/astroquery (`desired_position.py`)
2. Convert RA/Dec to Alt/Az for current time and observer location
3. Compare with current position from `HostTelescopeState`
4. Apply PID correction (`error_correction.py`)
5. Send move command if error exceeds tolerance (0.01 deg)
6. Re-resolve periodically for sidereal motion

**Autofocus** (`focus_controller.py`):
- Coarse-to-fine search: steps of [100, 50, 25, 10]
- Moves focus in/out, compares metric, converges on best position

**Simulation mode** (`--simulate`):
- `Simulator` replaces the TCP connection with an in-process mock Pi
- Simulates slew motion, focus, and state reporting
- Enables full Host testing without any hardware or network

### pi/ -- Hardware Control

The Pi is logic-agnostic. It executes commands, doesn't decide what to track. All celestial math stays on the Host.

**Main loop** (`main.py`):
- Single-threaded at 50 Hz with `LoopTimer`
- Each tick: feed watchdog, safety check, process one command from queue, periodic state report at 5 Hz
- `_dispatch_command()`: validate -> ack -> execute (move/focus/stop)

**Motor control** (`motor_controller.py`):
- Converts degrees to steps using `STEPS_PER_DEGREE` constants
- Chunked stepping (50 steps/chunk) with `stop_event` for responsive cancellation
- Moves alt axis first, then az axis (sequential, not simultaneous)
- Speed maps linearly from 0-1 to MIN_STEP_RATE_HZ - MAX_STEP_RATE_HZ

**Safety manager** (`safety_manager.py`):
- Last line of defense -- checked every tick
- Limit switches: triggers emergency stop if any switch is hit
- Position bounds: alt [0, 90], az [0, 360]
- Watchdog: emergency stop if not fed within timeout
- Emergency stop: disables all motors, sets EMERGENCY_STOP status

**Hardware abstraction**:
- `MotorDriver` ABC with `StepperMotorDriver` (real) and `MockMotorDriver` (testing)
- `SensorReader` ABC with `GPIOSensorReader` (real) and `MockSensorReader` (testing)
- `GPIOProvider` ABC with `HardwareGPIOProvider` (RPi.GPIO) and `MockGPIOProvider` (testing)
- RPi.GPIO is imported lazily (only in `HardwareGPIOProvider.__init__`), so all Pi code is importable on non-Pi systems

## Communication Flow

### Command round-trip (Host sends move):

```
Host                              Pi
 │                                 │
 │  MoveCommand (JSON over TCP)    │
 │ ──────────────────────────────> │
 │                                 │  validate -> is_valid_command()
 │         ack response            │
 │ <────────────────────────────── │
 │                                 │  motor_ctrl.execute_move()
 │                                 │    set_status(MOVING)
 │                                 │    step alt motor (chunked)
 │                                 │    step az motor (chunked)
 │                                 │    update_position()
 │                                 │    set_status(IDLE)
 │                                 │
 │         state_report            │  (periodic, 5 Hz)
 │ <────────────────────────────── │
 │                                 │
 │  update HostTelescopeState      │
 │                                 │
```

### Error flow (invalid command):

```
Host                              Pi
 │                                 │
 │  Invalid command (raw TCP)      │
 │ ──────────────────────────────> │
 │                                 │  is_valid_command() -> False
 │       error response            │
 │ <────────────────────────────── │  build_error_response(cmd_id, msg)
 │                                 │
 │  routes to response_queue       │
 │                                 │
```

## Threading Model

**Host** (3 threads during operation):
1. Main thread -- CLI input loop
2. Receiver thread -- `recv_message()` loop, dispatches to state/queue
3. Tracking thread (optional) -- periodic PID updates when tracking

**Pi** (2 threads during operation):
1. Main thread -- 50 Hz dispatch loop
2. TCPClient receiver thread -- `recv()` loop, puts messages on queue

All shared state is protected by `threading.Lock`. The Pi's main loop is deliberately single-threaded to avoid hardware contention.

## Testing Strategy

| Layer | Approach | Count |
|-------|----------|-------|
| shared/ | Pure unit tests on data classes, protocol, validation | 69 |
| pi/ | Unit tests with MockMotorDriver, MockSensorReader, MockGPIOProvider | 86 |
| host/ | Unit tests with mocked Sender, socket pairs, mock resolvers | 148 |
| integration/ | Real loopback TCP, IntegrationHarness wires both sides | 25 |
| **Total** | | **328** |

**Integration test harness** (`tests/integration/conftest.py`):
- Creates a TCP server on an ephemeral port (`127.0.0.1:0`)
- Wires real Host Sender+Receiver against real Pi dispatch loop
- Pi dispatch runs in a background thread with `_dispatch_command()` imported from `pi.main`
- State reports triggered manually for deterministic assertions
- `wait_for_condition()` polling replaces `time.sleep()` for reliable async testing

## Key Design Decisions

1. **Host is the TCP server, Pi is the client** -- Pi connects to Host on startup, enabling the Host to be started first and wait for Pi
2. **Ack before execute** -- Pi sends ack immediately upon receiving a valid command, then executes it. This unblocks the Host's `wait_for_ack()` quickly
3. **Chunked stepping** -- Motor moves are broken into 50-step chunks, checking `stop_event` between chunks for responsive cancellation
4. **Sequential axis movement** -- Alt moves first, then Az (not simultaneous). Simpler, avoids concurrent motor driver access
5. **All time in UTC** -- Internal timestamps use UTC. Display layer converts to local time
6. **Hardware behind ABCs** -- Every hardware interface has a mock implementation, enabling full test coverage without physical hardware
7. **Shared is sacred** -- Any change to shared/ requires updating both Host and Pi. The protocol is the contract
