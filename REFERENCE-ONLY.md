# ⚠️ Reference only — not the canonical project

This repository is a **design predecessor / reference implementation**, kept for
its patterns. The **canonical, actively-developed project** lives at
`agui_demo1/Phase0` (repo `ugocen/agui_demo1`).

## Why this matters

This repo and `agui_demo1/Phase0` share the same north star (AG-UI + CopilotKit
+ AgentCore) but have **different architectures**. This one is the earlier
design; `Phase0` re-architected it. Do **not** build on this repo for the
canonical project, and do **not** apply this repo's tooling to it.

| | This repo (reference) | `agui_demo1/Phase0` (canonical) |
|---|---|---|
| AG-UI events | emitted locally by a **translator** (`backend/app/agui/translator.py`) | agents on **AgentCore** emit them; the backend is a thin **SigV4 proxy** that pipes SSE |
| Catalog | static, hand-kept **`catalog.py` ↔ `catalog.ts`** parity | **DB-backed, AgentCore-synced, generic** (no agent/ARN in env) |
| Agents | local **scenario async-generators** + `registry.py` | **Strands / LangGraph** deployed to AgentCore (env-driven model provider) |
| Frontend | Next 14 / React 18 / Zustand / hand-built cards | Next 16 / React 19 / CopilotKit v2 + generic **A2UI** catalog |
| Collaboration | commit + push directly to `main` | **branch → PR → merge** |

## About the `.claude/` and `.agents/` tooling here

The skills/subagents in `.claude/` and `.agents/` (`add-card`, `new-scenario`,
`agui-verifier`, the invariants, the push-to-main collaboration rule, …) encode
**this repo's old architecture**. They are **not** valid for `agui_demo1/Phase0`,
which has its own Phase 0-correct tooling (`agui_demo1/AGENTS.md`,
`agui_demo1/.claude`, `agui_demo1/.agents`). If this repo is configured as an
agent "additional working directory" alongside `agui_demo1`, prefer the Phase 0
tooling for any work on the canonical project.

## Still useful here as reference

- Human-in-the-loop patterns (`useCopilotAction` + `renderAndWaitForResponse`).
- The scenario-agent catalog and the dual client (bespoke SSE client vs
  CopilotKit) selected by `NEXT_PUBLIC_CLIENT`.
- The `smoke_e2e.py` end-to-end SSE check.
