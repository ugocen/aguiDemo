# CLAUDE.md

Project guidance is canonical in @AGENTS.md — read it first (architecture
invariants, commands, where things live, gotchas, conventions). Deep context is
in `resources/HANDOFF.md`.

This file only adds the Claude Code specifics; everything else lives in AGENTS.md
so the two never drift.

## Claude Code specifics

- **Subagents** (`.claude/agents/`): `card-type-builder` (add a card/message type
  end to end), `scenario-agent-builder` (add a scenario agent), `agui-verifier`
  (run tests + smoke + frontend build and report pass/fail).
- **Commands** (`.claude/commands/`): `/verify`, `/smoke`, `/run`, `/add-card`,
  `/new-scenario`.
- **Permissions**: `.claude/settings.json` allowlists common dev commands;
  `.claude/settings.local.json` is personal and gitignored.

After changes, prefer `/verify` (or the `agui-verifier` subagent) to confirm the
repo is still healthy.
