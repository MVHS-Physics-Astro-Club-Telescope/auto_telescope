# Auto Telescope — Progress Log

> Updated automatically after every commit and at session end.
> Read this first when starting a new session to know exactly where things stand.

---

## Current Status

**Last Updated**: 2026-02-18
**Branch**: main
**Tests**: 303 passing (86 pi/ + 69 shared/ + 148 host/)
**Overall Progress**: 3 of 5 layers complete

---

## Completed

### host/ High-Level Control Layer (2026-02-18)
- PR #9, merged to main
- 18 source files + 16 test files (148 tests, including 8 pre-existing)
- **config/**: constants.py (network, PID, focus, observer defaults), ui_params.py
- **utils/**: logger.py ([HOST] prefix), math_utils.py (Vincenty angular distance, normalize, clamp, alt_az_delta), threading_utils.py (StoppableThread, PeriodicTask)
- **state/**: telescope_state.py (HostTelescopeState — thread-safe Pi state store), session_logs.py (circular buffer log)
- **comms/**: validator.py (outgoing/incoming validation), receiver.py (background recv thread, state_report/ack/error dispatch), sender.py (send_move/focus/stop with validation and ack waiting)
- **control/**: error_correction.py (PIDController), tracking_controller.py (resolve target, PID tracking loop, sidereal re-resolve), focus_controller.py (coarse-to-fine autofocus)
- **simulation/**: test_data.py (sample targets, factory functions), simulator.py (in-process Pi mock with slew simulation)
- **ui/**: display.py (format_state/tracking_info/log), host_interface.py (CLI: move, focus, stop, track, autofocus, status, log, help, quit)
- **main.py**: TCP server, Pi accept, tracking background thread, argparse (--host/--port/--lat/--lon/--elev/--simulate)

### shared/ Protocol Layer (2026-02-18)
- PR #6, merged to main
- 11 source files + 6 `__init__.py` + 1 test file (69 tests)
- Defines all commands (Move, Focus, Stop), enums (CommandType, StatusCode), errors (ErrorCode), state (TelescopeState, CameraState), TCP protocol (4-byte length-prefixed JSON), and message validator
- This is the communication contract consumed by both host/ and pi/

### pi/ Hardware Control Layer (2026-02-18)
- PR #7, merged to main
- 17 source files + 8 test files (86 tests)
- Hardware ABCs (GPIOProvider, MotorDriver, SensorReader) with mock implementations
- SafetyManager (limit switches, position bounds, watchdog, emergency stop)
- MotorController (degree-to-step, chunked stepping, stop events)
- FocusController (focus in/out with position limits)
- TCPClient (background receiver, reconnect logic)
- Message parser + response builders (ack/error/state)
- Main loop: 50Hz single-threaded with periodic state reports
- CLI: `python3 pi/main.py --mock --host 127.0.0.1`

### Infrastructure (2026-02-18)
- PR #5, merged to main
- CLAUDE.md, MEMORY.md, scratchpad.md
- .claude/commands/ (prime, plan, status, commit, review)
- .claude/agents/ (hardware-researcher, code-reviewer, test-runner, docs-writer)
- CI pipeline (.github/workflows/)

### host/control/desired_position.py (pre-existing)
- Celestial coordinate resolution using astropy + astroquery
- Three resolution strategies: solar system DB, JPL Horizons, SIMBAD
- 8 tests passing

---

## In Progress

Nothing currently in progress.

---

## Next Up (Priority Order)

1. **Integration testing** — End-to-end host↔pi communication tests
2. **Documentation** — Update README.md (still references Java), fill docs/architecture.md
3. **Dev tooling** — Add ruff, mypy to requirements-dev.txt

---

## Blockers

- None currently

---

## Known Issues

- README.md mentions Java but project is pure Python — needs updating
- docs/architecture.md exists but is empty
- CI uses Python 3.9/3.10 — requirements.txt is minimal (astropy, astroquery, pytest)
- RPi.GPIO / gpiozero not in requirements.txt (only needed on Pi hardware)
- Consider adding ruff, mypy to requirements-dev.txt

---

## Session Log

### Session 2026-02-18
- Set up Claude Code infrastructure (CLAUDE.md, commands, agents)
- Implemented shared/ protocol layer (11 files, 69 tests) — PR #6
- Implemented pi/ hardware control layer (17 files, 86 tests) — PR #7
- Created progress tracking system (docs/PROGRESS.md, /save command, task board)
- Implemented host/ high-level control layer (18 source files, 16 test files, 148 tests)
  - All 18 stubs replaced with full implementations
  - TCP server, CLI interface, tracking controller, PID, autofocus, simulator
  - 303 total tests passing across all layers
  - PR #9, squash-merged to main
