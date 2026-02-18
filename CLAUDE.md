# AUTO_TELESCOPE — Claude Code Master Prompt

> Autonomous telescope control system — Host ↔ Pi architecture with celestial tracking, motor control, and intelligent automation.

---

## Session Priming (Auto-runs at session start)

When a new session begins, Claude MUST execute this sequence before doing anything else:

1. **Scan repo**: `find . -maxdepth 3 -type f | head -80` for current file structure
2. **Read READMEs**: Main README.md, host/README.md, pi/README.md, shared/README.md
3. **Read MEMORY.md**: Load persistent decisions and architectural context
4. **Read scratchpad.md**: Load current task state, blockers, and next steps
5. **Check git**: `git status && git log --oneline -10`
6. **Announce readiness**: Summarize state and suggest next step

---

## Project Architecture

```
auto_telescope/
├── CLAUDE.md              # This file — master prompt
├── MEMORY.md              # Persistent decisions & learnings
├── scratchpad.md          # Current task state
├── .claude/               # Claude Code config
│   ├── settings.json      # Hooks, permissions
│   ├── commands/          # Slash commands (/prime, /plan, /status, /commit, /review)
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
├── shared/                # Communication contract (Host ↔ Pi)
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

## Mode System

### `cr` — Code Run (YOLO Mode)
When a prompt starts with `cr`:
- Execute without asking for confirmation on file writes, bash, git operations
- Move fast: implement → test → commit in one flow
- Still respect safety hooks (no force-push, no `rm -rf`)
- Use for: rapid prototyping, known patterns, small changes

### `cs` — Code Safe (Default)
When a prompt starts with `cs` (or no prefix):
- Ask before destructive file operations or git pushes
- Show plan before multi-file changes
- Pause at decision points for review
- Use for: architectural changes, new features, unfamiliar territory

---

## Quality Gates

### Before ANY Commit:
1. All modified files pass linting (if configured)
2. All existing tests pass: `pytest tests/ -v`
3. New code has tests for critical paths
4. scratchpad.md is updated
5. Conventional commit message: `type(scope): description`

### Before ANY PR:
1. All commit gates above
2. MEMORY.md updated if architectural decisions were made
3. README updated if public-facing behavior changed
4. No `TODO`/`FIXME` without linked issue

### Conventional Commit Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Build, CI, config
- `hw`: Hardware-related (custom)

---

## Context Management

### How compaction works:
- Claude Code compresses older messages when approaching context limits
- MEMORY.md and scratchpad.md survive compaction — they're re-read on priming
- Critical architectural decisions MUST go in MEMORY.md, not just conversation

### Surviving compaction:
- Keep MEMORY.md and scratchpad.md updated after every significant step
- Use scratchpad.md `## Current Task` as the always-available breadcrumb
- If confused after compaction, re-run `/prime` to reload full context

---

## Telescope-Specific Knowledge

### Hardware Safety (CRITICAL):
- ALWAYS add timeouts to motor commands (max 30s default)
- NEVER leave GPIO pins in undefined state — cleanup in `finally` blocks
- Serial ports and cameras MUST use context managers or explicit close
- Camera capture must handle connection loss gracefully
- Pi safety_manager.py is the last line of defense — never bypass it

### Celestial Math:
- Use `astropy` for coordinate transforms (RA/Dec ↔ Alt/Az)
- Time MUST be UTC internally, convert only at display layer
- Account for atmospheric refraction in pointing calculations
- Sidereal time calculations must use observer's longitude
- `get_object_coordinates()` in host/control/desired_position.py is the reference implementation

### Architecture Rules:
- Host is hardware-agnostic — no Pi-specific values in host/
- Pi is logic-agnostic — no celestial math in pi/
- Shared is the single source of truth for message formats
- Any shared/ change requires updating BOTH host/ and pi/
- Commands flow: Host → Shared → Pi. State flows: Pi → Shared → Host.

### Testing:
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
| Communication | TCP sockets | Host ↔ Pi via shared/protocols/ |
| Testing | pytest | With hardware mocking |
| CI/CD | GitHub Actions | .github/workflows/python-tests.yml |

---

## Git Workflow

### Branch Strategy:
```
main                    ← Production-ready, protected
├── develop             ← Integration branch (create when ready)
│   ├── feat/XXX        ← Feature branches
│   ├── fix/XXX         ← Bug fixes
│   ├── hw/XXX          ← Hardware changes
│   └── docs/XXX        ← Documentation
```

### Rules:
- NEVER push directly to main — use feature branches and PRs
- Branch names: `feat/add-star-tracking`, `fix/motor-stall-timeout`, `hw/stepper-driver`
- Squash merge to keep history clean
- PR template: What, Why, How, Testing, Hardware Impact

---

## Operational Principles

1. **Hardware safety first** — Every motor command needs a failsafe. Every sensor read needs a timeout.
2. **Test with mocks** — Hardware isn't always connected. All hardware interfaces must be mockable.
3. **Incremental progress** — Small commits, working state at every step.
4. **Document as you go** — MEMORY.md, scratchpad.md, and READMEs are not optional.
5. **Branch discipline** — Never commit directly to main.
6. **Shared is sacred** — Changes to shared/ affect both sides. Coordinate carefully.
7. **Host stays clean** — No hardware-specific code in host/.
8. **Pi stays focused** — No high-level logic in pi/. It executes, doesn't decide.
9. **Fail loud** — Hardware I/O must never fail silently. Log and propagate errors.
10. **UTC everywhere** — Internal time is always UTC. Convert only at display boundaries.
