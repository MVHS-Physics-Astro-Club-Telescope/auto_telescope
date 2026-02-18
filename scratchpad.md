# Scratchpad

## Current Task
Shared/ protocol layer implementation — COMPLETE

## Status
- [x] Repo scan and analysis complete
- [x] CLAUDE.md created (tailored to actual repo structure)
- [x] MEMORY.md created (captures current state and decisions)
- [x] scratchpad.md created (this file)
- [x] .claude/settings.json created (hooks, permissions)
- [x] Slash commands created (/prime, /plan, /status, /commit, /review)
- [x] Subagents created (hardware-researcher, code-reviewer, test-runner, docs-writer)
- [x] shared/ protocol layer implemented (11 source files + 6 __init__.py + 1 test file = 18 files)

## Completed: shared/ Protocol Layer (2026-02-18)
- 6x `__init__.py` (shared/, enums/, errors/, commands/, protocols/, state/)
- `shared/enums/command_types.py` — CommandType str Enum (MOVE, FOCUS, STOP, STATUS_REQUEST)
- `shared/enums/status_codes.py` — StatusCode str Enum (7 members)
- `shared/errors/error_codes.py` — ErrorCode IntEnum (22 codes) + descriptions dict
- `shared/protocols/constants.py` — All magic numbers (port, framing, ranges, timeouts)
- `shared/commands/move_command.py` — MoveCommand dataclass with to_dict/from_dict
- `shared/commands/focus_command.py` — FocusCommand dataclass + FOCUS_IN/FOCUS_OUT constants
- `shared/commands/stop_command.py` — StopCommand dataclass (no timeout — stops are instant)
- `shared/state/telescope_state.py` — TelescopeState dataclass
- `shared/state/camera_state.py` — CameraState dataclass
- `shared/protocols/message_validator.py` — validate_move/focus/stop/message + ValidationError
- `shared/protocols/tcp_protocol.py` — 4-byte length-prefixed JSON framing + ProtocolError
- `tests/shared/test_messages.py` — 69 tests, all passing
- Also added tests/__init__.py and tests/shared/__init__.py

## Next Steps
- [ ] Commit shared/ protocol layer on a feature branch
- [ ] Begin pi/ hardware layer implementation (next logical layer)
- [ ] Or begin host/ comms layer (depends on shared/ — now unblocked)

## Blockers
None currently.

## Notes
- Python 3.9 compat: must use `Optional[X]`, `List[X]`, `Dict[K,V]` — not `X | None`, `list[x]`, `dict[k,v]`
- ~44 remaining stub files in host/ and pi/
- README.md still references Java — needs updating to Python-only
- Consider adding ruff, mypy to requirements-dev.txt
