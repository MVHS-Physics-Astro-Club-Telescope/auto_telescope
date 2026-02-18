Create an implementation plan for: $ARGUMENTS

Steps:
1. Read MEMORY.md and scratchpad.md for current context
2. Research what exists in the codebase related to this task (scan host/, pi/, shared/)
3. Identify dependencies and prerequisites — what must exist before this can work
4. Break into ordered implementation steps with file paths
5. Estimate complexity per step: S (< 30 min), M (30 min - 2 hr), L (> 2 hr)
6. Identify risks: hardware safety concerns, breaking changes to shared/, test gaps
7. Write the plan to scratchpad.md under `## Current Task`

Architecture reminders:
- Host handles logic (coordinates, tracking, error correction)
- Pi handles hardware (motors, GPIO, sensors)
- Shared defines the contract (commands, state, protocols)
- Changes to shared/ require updates on BOTH sides
- All hardware code needs timeouts and cleanup
