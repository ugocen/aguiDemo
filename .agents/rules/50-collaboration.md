# Collaboration protocol — pull before, log and push after

More than one agent may work `main` in parallel (Claude Code, Antigravity, …).

- **Before a task:** `git pull`, review the incoming changes, and read the newest
  entries in the work log at the end of `resources/HANDOFF.md`.
- **After a task:** run the standard verification and, only if green, prepend a
  short work-log entry (your tool + session id, what you did, what you plan next)
  and push to `main`. On push rejection: `git pull --rebase` (keep both work-log
  entries; never force-push `main`).

The **canonical** steps, conflict handling, and entry format live in that work
log (HANDOFF, final section). Follow it there — do not restate it here.
