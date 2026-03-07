# AUTO_TELESCOPE

> Autonomous telescope control system — Host <-> Pi architecture with celestial tracking, motor control, and intelligent automation.

---

## Project Architecture

```
auto_telescope/
├── CLAUDE.md              # This file
├── MEMORY.md              # Persistent decisions & learnings
├── scratchpad.md          # Current task state
├── .claude/               # Claude Code config
│   ├── settings.json      # Hooks, permissions
│   ├── commands/          # Slash commands
│   └── agents/            # Subagents (hardware-researcher, code-reviewer, test-runner, docs-writer)
├── host/                  # Host computer — high-level control
│   ├── main.py            # Entry point, thread coordination
│   ├── config/            # Constants, UI params
│   ├── control/           # Core algorithms (desired_position, tracking, focus, error correction)
│   ├── comms/             # TCP sender/receiver to Pi
│   ├── state/             # Telescope state, session logs
│   ├── ui/                # Manual/auto interface, display
│   ├── simulation/        # Testing without hardware
│   └── utils/             # Logger, math, threading
├── pi/                    # Raspberry Pi — hardware control
│   ├── main.py            # Entry point, hardware init
│   ├── config/            # Constants, GPIO pin mappings
│   ├── control/           # Motor controller, focus, safety
│   ├── hardware/          # GPIO setup, motor driver, sensors
│   ├── comms/             # TCP client, message parser
│   ├── state/             # Position tracking, error state
│   └── utils/             # Logger, timer, debug
├── shared/                # Communication contract (Host <-> Pi)
│   ├── commands/          # move, focus, stop command definitions
│   ├── enums/             # command_types, status_codes
│   ├── errors/            # error_codes
│   ├── protocols/         # TCP protocol, constants, validator
│   └── state/             # telescope_state, camera_state
├── tests/                 # Mirrors host/, pi/, shared/
├── docs/                  # Architecture docs
├── .github/workflows/     # CI pipeline
└── requirements.txt       # astropy, astroquery, pytest
```

---

## Hardware Safety (CRITICAL)

- ALWAYS add timeouts to motor commands (max 30s default)
- NEVER leave GPIO pins in undefined state — cleanup in `finally` blocks
- Serial ports and cameras MUST use context managers or explicit close
- Camera capture must handle connection loss gracefully
- Pi safety_manager.py is the last line of defense — never bypass it

## Celestial Math

- Use `astropy` for coordinate transforms (RA/Dec <-> Alt/Az)
- Time MUST be UTC internally, convert only at display layer
- Account for atmospheric refraction in pointing calculations
- Sidereal time calculations must use observer's longitude
- `get_object_coordinates()` in host/control/desired_position.py is the reference implementation

## Architecture Rules

- Host is hardware-agnostic — no Pi-specific values in host/
- Pi is logic-agnostic — no celestial math in pi/
- Shared is the single source of truth for message formats
- Any shared/ change requires updating BOTH host/ and pi/
- Commands flow: Host -> Shared -> Pi. State flows: Pi -> Shared -> Host.

## Testing

- `PYTHONPATH` must include repo root: `export PYTHONPATH=$PYTHONPATH:$(pwd)`
- Tests requiring network (astropy queries) may be slow — mark with `@pytest.mark.slow`
- All hardware interfaces must be mockable for offline testing
- Run tests: `pytest tests/ -v --tb=short`

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3.9+ | CI tests 3.9, 3.10 |
| Coordinates | astropy, astroquery | Celestial calculations, SIMBAD/Horizons |
| Hardware IO | RPi.GPIO / gpiozero | Raspberry Pi GPIO (not yet in requirements) |
| Motor Control | Stepper drivers (TBD) | Via pi/hardware/motor_driver.py |
| Communication | TCP sockets | Host <-> Pi via shared/protocols/ |
| Testing | pytest | With hardware mocking |
| CI/CD | GitHub Actions | .github/workflows/python-tests.yml |

---

## Branch Strategy

```
main                    <- Production-ready, protected
├── develop             <- Integration branch (create when ready)
│   ├── feat/XXX        <- Feature branches
│   ├── fix/XXX         <- Bug fixes
│   ├── hw/XXX          <- Hardware changes
│   └── docs/XXX        <- Documentation
```

- Branch names: `feat/add-star-tracking`, `fix/motor-stall-timeout`, `hw/stepper-driver`
- Squash merge to keep history clean
- Custom commit type: `hw(scope):` for hardware-related changes

---

## Operational Principles

1. **Hardware safety first** — Every motor command needs a failsafe. Every sensor read needs a timeout.
2. **Test with mocks** — Hardware isn't always connected. All hardware interfaces must be mockable.
3. **Shared is sacred** — Changes to shared/ affect both sides. Coordinate carefully.
4. **Host stays clean** — No hardware-specific code in host/.
5. **Pi stays focused** — No high-level logic in pi/. It executes, doesn't decide.
6. **Fail loud** — Hardware I/O must never fail silently. Log and propagate errors.
7. **UTC everywhere** — Internal time is always UTC. Convert only at display boundaries.
