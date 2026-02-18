# Auto Telescope — Progress Log

> Updated automatically after every commit and at session end.
> Read this first when starting a new session to know exactly where things stand.

---

## Current Status

**Last Updated**: 2026-02-18
**Branch**: main
**Tests**: 163 passing (86 pi/ + 69 shared/ + 8 host/)
**Overall Progress**: 2 of 5 layers complete

---

## Completed

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

1. **host/comms/** — TCP server + message handling (mirror of pi/comms/ but server-side)
2. **host/state/** — Telescope state tracking, session logging
3. **host/control/** — Tracking loop, error correction, focus control (desired_position.py already done)
4. **host/config/** — Constants, UI params
5. **host/utils/** — Logger, math helpers, threading utils
6. **host/ui/** — Manual/auto interface, display
7. **host/simulation/** — Testing without hardware
8. **host/main.py** — Entry point, thread coordination
9. **Integration testing** — End-to-end host↔pi communication tests
10. **Documentation** — Update README.md (still references Java), fill docs/architecture.md

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
