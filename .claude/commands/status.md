Show full project status:

1. Read docs/PROGRESS.md — source of truth for completed work and next steps
2. Read .claude/skills/task-board/SKILL.md — implementation checklist
3. Read scratchpad.md — current task, completed steps, blockers
4. Read MEMORY.md — recent decisions and known issues
5. Run `git status` — uncommitted changes, current branch
6. Run `git log --oneline -5` — recent commits
7. Run `export PYTHONPATH=$PWD:$PYTHONPATH && python3 -m pytest tests/ -v --tb=short 2>&1 | tail -30` — test results

Present as a clear status report:
```
## Project Status
**Last Session**: (from PROGRESS.md session log)
**Branch**: ...
**Current Task**: ...
**Tests**: X passing, Y failing
**Implementation Progress**: X/Y files implemented (from task board)
**Blockers**: ...
**Next Step**: ...
```
