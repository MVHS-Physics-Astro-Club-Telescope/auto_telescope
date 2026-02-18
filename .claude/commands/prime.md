Re-run the full priming sequence to reload project context:

1. Read docs/PROGRESS.md — this is the source of truth for what's done, what's in progress, and what's next
2. Read MEMORY.md for persistent architectural decisions
3. Read scratchpad.md for working task state
4. Read CLAUDE.md for project rules and conventions (already loaded, skim for reminders)
5. Scan file structure: `find . -maxdepth 3 -type f -name '*.py' | head -80`
6. Check git: `git status && git log --oneline -10`
7. Run tests: `export PYTHONPATH=$PWD:$PYTHONPATH && python3 -m pytest tests/ -v --tb=short 2>&1 | tail -30`
8. Read .claude/skills/task-board/SKILL.md for the implementation checklist

Summarize:
- Where you left off (from PROGRESS.md session log)
- Current branch and any uncommitted changes
- Test status
- The next logical task to work on

Confirm with the user before proceeding to any work.

IMPORTANT: Use this after context compaction, session start, or whenever you feel out of sync with the repo.
