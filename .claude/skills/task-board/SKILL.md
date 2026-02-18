# Auto Telescope — Task Board

> Checklist of all implementation work. Updated automatically after every commit.

---

## Layer Implementation

### shared/ — Protocol Contract
- [x] shared/enums/command_types.py
- [x] shared/enums/status_codes.py
- [x] shared/errors/error_codes.py
- [x] shared/commands/move_command.py
- [x] shared/commands/focus_command.py
- [x] shared/commands/stop_command.py
- [x] shared/state/telescope_state.py
- [x] shared/state/camera_state.py
- [x] shared/protocols/constants.py
- [x] shared/protocols/tcp_protocol.py
- [x] shared/protocols/message_validator.py
- [x] tests/shared/test_messages.py (69 tests)

### pi/ — Hardware Control
- [x] pi/utils/logger.py
- [x] pi/utils/timer.py
- [x] pi/utils/debug_helpers.py
- [x] pi/config/constants.py
- [x] pi/config/pins.py
- [x] pi/hardware/gpio_setup.py
- [x] pi/hardware/motor_driver.py
- [x] pi/hardware/sensor_reader.py
- [x] pi/state/error_state.py
- [x] pi/state/telescope_state.py
- [x] pi/control/safety_manager.py
- [x] pi/control/motor_controller.py
- [x] pi/control/focus_controller.py
- [x] pi/comms/validator.py
- [x] pi/comms/message_parser.py
- [x] pi/comms/tcp_client.py
- [x] pi/main.py
- [x] tests/pi/ (8 test files, 86 tests)

### host/ — High-Level Control
- [x] host/control/desired_position.py (pre-existing)
- [x] host/config/constants.py
- [x] host/config/ui_params.py
- [x] host/utils/logger.py
- [x] host/utils/math_utils.py
- [x] host/utils/threading_utils.py
- [x] host/comms/validator.py
- [x] host/comms/receiver.py
- [x] host/comms/sender.py
- [x] host/state/telescope_state.py
- [x] host/state/session_logs.py
- [x] host/control/error_correction.py
- [x] host/control/tracking_controller.py
- [x] host/control/focus_controller.py
- [x] host/ui/display.py
- [x] host/ui/host_interface.py
- [x] host/simulation/test_data.py
- [x] host/simulation/simulator.py
- [x] host/main.py
- [x] tests/host/ (16 test files, 148 tests)

### Integration & Polish
- [ ] End-to-end host↔pi communication tests
- [ ] Update README.md (remove Java references)
- [ ] Fill docs/architecture.md
- [ ] Add ruff/mypy to dev dependencies

---

## Test Summary

| Layer | Tests | Status |
|-------|-------|--------|
| shared/ | 69 | Passing |
| pi/ | 86 | Passing |
| host/ | 148 | Passing |
| **Total** | **303** | **All passing** |
