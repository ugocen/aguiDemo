# Collaboration protocol — pull before, log and push after

More than one agent may work this repo in parallel (Claude Code, Antigravity, …).
Always:

- **Before starting a task:** `git pull` on `main`, review the incoming changes,
  and read the newest entries in the work log at the end of
  `resources/HANDOFF.md` (section 11) — what others just did and plan to do.
- **After finishing a task:** prepend a short entry to that work log — your
  session identity (e.g. `Claude-Session: …` or `Antigravity-Session: …`), what
  you did, and what you plan next (if any). Then commit and push to `main`.
- If the push is rejected because `main` moved, `git pull --rebase` and push
  again. Work-log conflicts are trivial: keep both entries.
- Log the **work done**, not the file list (git tracks files).
