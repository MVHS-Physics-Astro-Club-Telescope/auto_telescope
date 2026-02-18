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
- [ ] host/config/constants.py
- [ ] host/config/ui_params.py
- [ ] host/utils/logger.py
- [ ] host/utils/math_helpers.py
- [ ] host/utils/threading_utils.py
- [ ] host/comms/tcp_sender.py
- [ ] host/comms/tcp_receiver.py
- [ ] host/state/telescope_state.py
- [ ] host/state/session_log.py
- [ ] host/control/tracking.py
- [ ] host/control/focus.py
- [ ] host/control/error_correction.py
- [ ] host/ui/manual_control.py
- [ ] host/ui/auto_control.py
- [ ] host/ui/display.py
- [ ] host/simulation/mock_pi.py
- [ ] host/simulation/sky_model.py
- [ ] host/main.py

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
| host/ | 8 | Passing |
| **Total** | **163** | **All passing** |
