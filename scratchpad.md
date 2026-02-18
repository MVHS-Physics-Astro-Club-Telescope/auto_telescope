# Scratchpad

## Current Task
None — between tasks. Documentation updates complete.

## Status
- [x] Infrastructure: CLAUDE.md, MEMORY.md, scratchpad.md, commands, agents
- [x] shared/ protocol layer (11 source files, 69 tests) — PR #6 merged
- [x] pi/ hardware control layer (17 source files, 86 tests) — PR #7 merged
- [x] Progress tracking system (docs/PROGRESS.md, task board, /save command)
- [x] host/ layer implementation (18 source files, 148 tests) — PR #9 merged
- [x] Integration testing (6 files, 25 tests) — PR #10 merged
- [x] Documentation updates (README.md, docs/architecture.md)
- [ ] Dev tooling (ruff, mypy)

## Next Steps
1. Add ruff/mypy to dev dependencies

## Blockers
None currently.

## Notes
- 328 tests passing (86 pi/ + 69 shared/ + 148 host/ + 25 integration/)
- All on main branch — PRs #5, #6, #7, #8, #9, #10, #11 merged
- Python 3.9 compat: use `Optional[X]`, `List[X]`, `Dict[K,V]`
- Host is TCP server (Pi connects as client)
- Simulation mode: `python3 -m host.main --simulate`
- Integration tests use real loopback TCP (no mocked sockets)
