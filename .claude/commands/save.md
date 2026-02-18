Force-save current progress to all tracking files. Run this anytime to checkpoint your work.

Execute these steps in order:

1. **Update docs/PROGRESS.md**:
   - Update "Last Updated" date and "Current Status" section
   - Move any completed items from "In Progress" to "Completed" with date
   - Update "Next Up" list based on what remains
   - Add a bullet to the "Session Log" section for today describing what was done
   - Update test counts and branch info

2. **Update .claude/skills/task-board/SKILL.md**:
   - Check off any completed items in the implementation checklist
   - Add new items if scope has expanded

3. **Update scratchpad.md**:
   - Set "Current Task" to whatever is actively being worked on (or "None" if between tasks)
   - Update status checkboxes
   - Update "Next Steps" and "Blockers"

4. **Update MEMORY.md** (only if architectural decisions were made):
   - Add new decisions with date
   - Update implementation status
   - Clear any resolved known issues

5. **Confirm** by printing a summary of what was updated.

IMPORTANT: This same save sequence must run automatically after every commit and at session end. This slash command is a manual trigger for the same process.
