# Scratchpad

## Current Task
None — between tasks. Progress tracking system just set up.

## Status
- [x] Infrastructure: CLAUDE.md, MEMORY.md, scratchpad.md, commands, agents
- [x] shared/ protocol layer (11 source files, 69 tests) — PR #6 merged
- [x] pi/ hardware control layer (17 source files, 86 tests) — PR #7 merged
- [x] Progress tracking system (docs/PROGRESS.md, task board, /save command)
- [ ] host/ layer implementation (~18 stub files remaining)
- [ ] Integration testing
- [ ] Documentation updates

## Next Steps
1. host/comms/ — TCP server + message handling (server-side mirror of pi/comms/)
2. host/state/ — Telescope state tracking, session logging
3. host/control/ — Tracking loop, error correction, focus
4. host/config/, host/utils/, host/ui/, host/simulation/, host/main.py
5. Integration testing and documentation

## Blockers
None currently.

## Notes
- 163 tests passing (86 pi/ + 69 shared/ + 8 host/)
- Python 3.9 compat: use `Optional[X]`, `List[X]`, `Dict[K,V]`
- README.md still references Java — needs updating
- docs/PROGRESS.md is now the primary session-persistent progress tracker
