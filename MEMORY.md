# Auto Telescope — Memory

## Architecture Decisions
- [2026-02-18] Three-layer architecture: Host (high-level control) ↔ Shared (protocol contract) ↔ Pi (hardware control)
- [2026-02-18] Host is hardware-agnostic. Pi is logic-agnostic. Shared is the single source of truth for messages.
- [2026-02-18] TCP communication between Host and Pi via shared/protocols/
- [2026-02-18] Commands flow Host → Pi. State feedback flows Pi → Host. Both use shared/ definitions.
- [2026-02-18] Celestial coordinate resolution uses astropy + astroquery (SIMBAD, JPL Horizons)

## Hardware
- Raspberry Pi: Main hardware controller, runs pi/ subsystem
- Stepper motors: TBD driver (TMC2209 or A4988), controlled via pi/hardware/motor_driver.py
- GPIO pins: Mapped in pi/config/pins.py (not yet defined)
- Camera: TBD, will be used for autofocus and plate solving

## Patterns & Conventions
- All Python files use stub comments as placeholders: `# Description of what goes here`
- Only host/control/desired_position.py is fully implemented (celestial coordinate resolution)
- Tests mirror source structure: tests/host/, tests/pi/, tests/shared/
- PYTHONPATH must include repo root for imports to work
- Case-insensitive celestial object name handling with whitespace trimming
- Three resolution strategies: solar system DB → JPL Horizons → SIMBAD (fallback chain)

## Implementation Status
- **Implemented**: desired_position.py, test_desired_position.py, CI pipeline, project docs
- **Stubs only**: All other host/, pi/, shared/ modules (~55 files)
- **Empty tests**: test_focus.py, test_tracking.py, test_motor_commands.py, test_sensors.py, test_messages.py
- **Deleted files pending commit**: pytest.ini, scripts/*, tests/shared/test_protocal.py

## Known Issues
- README.md mentions Java but project is pure Python — needs updating
- docs/architecture.md exists but is empty
- pytest.ini was deleted from working tree but not committed
- tests/shared/test_protocal.py has typo in filename ("protocal" → "protocol")
- CI uses Python 3.9/3.10 but CLAUDE.md tech stack says 3.11+ — should align
- requirements.txt is minimal (astropy, astroquery, pytest only)

## Dependencies
- astropy: Celestial coordinate transformations (RA/Dec ↔ Alt/Az)
- astroquery: Query JPL Horizons and SIMBAD databases
- pytest: Test framework
