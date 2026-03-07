Create an implementation plan for: $ARGUMENTS

Architecture reminders:
- Host handles logic (coordinates, tracking, error correction)
- Pi handles hardware (motors, GPIO, sensors)
- Shared defines the contract (commands, state, protocols)
- Changes to shared/ require updates on BOTH sides
- All hardware code needs timeouts and cleanup
