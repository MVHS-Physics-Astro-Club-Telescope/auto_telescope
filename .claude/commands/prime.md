Re-run the full priming sequence to reload project context:

1. Scan file structure: `find . -maxdepth 3 -type f | head -80`
2. Read all READMEs: README.md, host/README.md, pi/README.md, shared/README.md
3. Read MEMORY.md for persistent decisions and architecture
4. Read scratchpad.md for current task state and blockers
5. Check git: `git status && git log --oneline -10`
6. Summarize what you found and suggest the logical next step

Use this after context compaction, session start, or whenever you feel out of sync with the repo.
