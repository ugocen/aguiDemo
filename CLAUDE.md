# CLAUDE.md

Project guidance is canonical in @AGENTS.md — read it first (architecture
invariants, commands, where things live, gotchas, conventions). Deep context is
in `resources/HANDOFF.md`.

This file only adds the Claude Code specifics; everything else lives in AGENTS.md
so the two never drift.

## Collaboration protocol — STRICT, every task, no exceptions

Multiple agents share `main`. These steps are mandatory and **MUST NOT be
skipped** — not for a "small" change, not when in a hurry, and not for the 2nd or
3rd task within one session. The canonical steps live in `resources/HANDOFF.md`
§11; this is the non-negotiable enforcement reminder.

1. **Before starting EVERY task:** `git pull` on `main`, then read the newest
   work-log entries at the end of `resources/HANDOFF.md`. Pull again before each
   task in a session — not only the first.
2. **After finishing a task:** run the standard verification (`/verify`, or
   backend `pytest -q` + `python scripts/smoke_e2e.py` and frontend
   `typecheck`/`lint`/`build`). Push only if green — never push red.
3. **Then log and push:** prepend a short work-log entry to `resources/HANDOFF.md`
   §11 (identity, what you did, what's next), `git commit`, and `git push origin
   main`. The work-log push is the one sanctioned auto-push, separate from "push
   only when asked". Fold trivial edits into the next entry, but still pull first.

If you catch yourself about to edit code without having pulled, stop and pull.

## Claude Code specifics

- **Subagents** (`.claude/agents/`): `card-type-builder` (add a card/message type
  end to end), `scenario-agent-builder` (add a scenario agent), `agui-verifier`
  (run tests + smoke + frontend build and report pass/fail).
- **Commands** (`.claude/commands/`): `/check` (prerequisites), `/verify`,
  `/smoke`, `/run` (dev servers), `/build` (Docker images), `/add-card`,
  `/new-scenario`, `/aws-bootstrap` (scoped AWS deployer).
- **Permissions**: `.claude/settings.json` allowlists common dev commands;
  `.claude/settings.local.json` is personal and gitignored.

After changes, prefer `/verify` (or the `agui-verifier` subagent) to confirm the
repo is still healthy.
