Review current uncommitted changes:

1. Run `git diff` to see all changes (staged + unstaged)
2. Run `git diff --stat` for a summary view
3. Review each changed file for:

**Safety (CRITICAL for pi/ files):**
- [ ] Motor commands have timeouts (max 30s)
- [ ] GPIO pins cleaned up in finally blocks
- [ ] Serial/camera resources use context managers
- [ ] safety_manager.py not bypassed

**Error Handling:**
- [ ] Hardware I/O never fails silently
- [ ] Exceptions logged with context
- [ ] Graceful degradation where appropriate

**Thread Safety (host/ and pi/ main.py):**
- [ ] Shared state protected by locks
- [ ] No race conditions in concurrent motor/camera access

**Architecture:**
- [ ] Host has no hardware-specific code
- [ ] Pi has no celestial math or high-level logic
- [ ] Shared changes reflected in both host/ and pi/
- [ ] No Pi-specific values hardcoded in host/

**Code Quality:**
- [ ] Functions have clear single responsibility
- [ ] Constants defined in config/, not magic numbers
- [ ] Imports are clean and organized

4. Flag issues with severity:
   - **CRITICAL**: Must fix before commit (safety, data loss, broken protocol)
   - **WARNING**: Should fix soon (error handling gaps, missing tests)
   - **INFO**: Nice to fix (style, naming, minor improvements)

5. Suggest specific fixes for CRITICAL issues
