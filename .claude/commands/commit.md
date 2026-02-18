Guided commit workflow:

1. Run `git diff --stat` to see what changed
2. Run `git diff` to review actual changes
3. Run tests if they exist: `export PYTHONPATH=$PYTHONPATH:$(pwd) && python3 -m pytest tests/ -v --tb=short`
4. Generate a conventional commit message based on changes:
   - feat(scope): for new features
   - fix(scope): for bug fixes
   - docs(scope): for documentation
   - refactor(scope): for restructuring
   - test(scope): for tests
   - chore(scope): for config/build
   - hw(scope): for hardware changes
   - Scope should be: host, pi, shared, tests, or project
5. Stage appropriate files — DO NOT stage scratchpad.md or MEMORY.md unless intentional
6. Show the commit message for approval before executing
7. After commit, update scratchpad.md with what was done

IMPORTANT: Never push directly to main. If on main, suggest creating a feature branch first.

## Post-Commit: Auto-Save Progress (MANDATORY)

After EVERY successful commit, you MUST immediately:

1. Update docs/PROGRESS.md — move completed items, update test counts, add session log entry
2. Update .claude/skills/task-board/SKILL.md — check off completed files
3. Update scratchpad.md — update current task and status
4. Update MEMORY.md if any architectural decisions were made

This is non-negotiable. Never skip the post-commit save.
