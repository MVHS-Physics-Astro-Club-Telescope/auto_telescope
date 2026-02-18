Show full project status:

1. Read scratchpad.md — current task, completed steps, blockers
2. Read MEMORY.md — recent decisions and known issues
3. Run `git status` — uncommitted changes, current branch
4. Run `git log --oneline -5` — recent commits
5. Run `pytest tests/ -v --tb=short 2>&1 | tail -30` — test results (if pytest available)
6. Count stub files vs implemented files in host/, pi/, shared/

Present as a clear status report:
```
## Project Status
**Branch**: ...
**Current Task**: ...
**Tests**: X passing, Y failing
**Implementation Progress**: X/Y files implemented
**Blockers**: ...
**Next Step**: ...
```
