# Auto Telescope — Memory

## Architecture Decisions
- [2026-02-18] Three-layer architecture: Host (high-level control) <-> Shared (protocol contract) <-> Pi (hardware control)
- [2026-02-18] Host is hardware-agnostic. Pi is logic-agnostic. Shared is the single source of truth for messages.
- [2026-02-18] TCP communication between Host and Pi via shared/protocols/
- [2026-02-18] Commands flow Host -> Pi. State feedback flows Pi -> Host. Both use shared/ definitions.
- [2026-02-18] Celestial coordinate resolution uses astropy + astroquery (SIMBAD, JPL Horizons)
- [2026-02-18] Pi hardware behind ABCs (GPIOProvider, MotorDriver, SensorReader) with mock implementations
- [2026-02-18] SafetyManager is last line of defense — limit switches, position bounds, watchdog, emergency stop
- [2026-02-18] Motor control uses chunked stepping (50 steps/chunk) with stop_event for responsive cancellation
- [2026-02-18] Pi main loop runs at 50Hz single-threaded with periodic state reports at 5Hz

## Hardware
- Raspberry Pi: Main hardware controller, runs pi/ subsystem
- Stepper motors: TBD driver (TMC2209 or A4988), controlled via pi/hardware/motor_driver.py
- GPIO pins: Mapped in pi/config/pins.py (BCM placeholders: alt=17/27/22/5, az=23/24/25/6, focus=12/16/20)
- Camera: TBD, will be used for autofocus and plate solving

## Patterns & Conventions
- Tests mirror source structure: tests/host/, tests/pi/, tests/shared/, tests/integration/
- Integration tests use IntegrationHarness (real loopback TCP, no mocked sockets)
- wait_for_condition() polling helper replaces fragile time.sleep() in async tests
- PYTHONPATH must include repo root for imports to work
- Case-insensitive celestial object name handling with whitespace trimming
- Three resolution strategies: solar system DB -> JPL Horizons -> SIMBAD (fallback chain)
- Thread-safe state management using threading.Lock in pi/state/

## Implementation Status
- **Complete**: shared/ (11 files, 69 tests), pi/ (17 files, 86 tests), host/ (18 files, 148 tests), integration (6 files, 25 tests)
- **Total tests**: 328 passing

## Progress Tracking System
- docs/PROGRESS.md: Primary session-persistent progress tracker (source of truth)
- .claude/skills/task-board/SKILL.md: Per-file implementation checklist
- scratchpad.md: Current task working state
- MEMORY.md: This file — architectural decisions and learnings
- /save command: Manual trigger to update all tracking files
- Auto-save: Runs after every commit and at session end (codified in CLAUDE.md)

## Known Issues
- RPi.GPIO / gpiozero not in requirements.txt (only needed on actual Pi)
- Consider adding ruff, mypy to requirements-dev.txt

## Dependencies
- astropy: Celestial coordinate transformations (RA/Dec <-> Alt/Az)
- astroquery: Query JPL Horizons and SIMBAD databases
- pytest: Test framework
