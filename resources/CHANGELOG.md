# Changelog — what has been built in this project so far

A themed summary of everything added over the session (see `git log` for
chronological detail). Canonical guide: `AGENTS.md`; deep context:
`resources/HANDOFF.md`; remaining work: `TODO.md`.

## Phase 1 — local app (core)
- **Backend** (FastAPI + LangGraph + `ag-ui-protocol`): single-source `translator`
  (all AG-UI events emitted here), `mock` + `langgraph` agents, SSE + 15s
  keepalive, in-memory HITL resume (`/agui/resume`), event capture + ordering
  lint, PostgreSQL history (swappable repository), dev/Entra auth.
- **Frontend** (Next.js App Router, TS strict, Zustand, Tiptap): two-region
  workspace (agents + history sidebar, chat, canvas), custom AG-UI/SSE client,
  a live **Event Inspector**.
- **Evidence**: `pytest` tests, `docs/sample_run_log.jsonl` (lint-clean).

## Message / card types (10 types, 8 tools)
text, lookup tool, **table**, **chart** (inline SVG), follow-up, suggested
questions, **citations**, **form**, approval (HITL), canvas. Each renders in both
clients; catalog parity is checked by `smoke_e2e.py`.

## Second client — CopilotKit
- `@copilotkit/*` 1.62.2 + `@ag-ui/client`; the `/api/copilotkit` runtime route
  bridges to the backend via `HttpAgent`.
- All cards via `useCopilotAction` (`CopilotGenerativeUI`); canvas via `useCoAgent`
  (`CopilotCanvasPanel`); scenario selection via provider `properties`; approval
  via a `respond()` + `/agui/resume` bridge. Selected by `NEXT_PUBLIC_CLIENT`.
- Build-verified (`tsc` + `next build`); full runtime verification needs a browser.

## Scenario agents (`agents/` — separate package)
`research-assistant`, `doc-writer`, `data-analyst`, `support-triage` — each a
different card combination. Routed by `forwardedProps.agentId`, listed via
`/agents` in the sidebar, reusing the same translator (AgentCore-ready).

## Vendor-agnostic LLM (Claude / OpenAI / Gemini / Marketplace)
`app/llm/factory.build_llm` is the single model path; the vendor is selected by
`LLM_PROVIDER`. `openai_compatible` (OpenAI + Marketplace), `anthropic_provider`
(Claude Messages API), `gemini_provider` (streamGenerateContent) — all expose the
same `stream_completion`. `test_llm_providers.py` verifies each vendor's SSE parse
with mock HTTP.

## Cloud assets (prepared, not deployed)
- `deploy/agentcore/` — Bedrock AgentCore packaging (`/ping`+`/invocations`) +
  Dockerfile (CLI or ECR-register).
- `deploy/eks/` — minimal Helm chart (backend/frontend/ingress/config), RDS+Entra.
- `deploy/aws/` — **safe AWS flow**: IAM policy + `bootstrap_iam.sh` (use root once
  to create `agui-deployer`) + README. After that always that profile, never root.

## Multi-tool agent setup
- `AGENTS.md` (canonical, cross-tool) + `CLAUDE.md` (`@AGENTS.md` import → no drift).
- **Claude Code**: `.claude/agents/` (card-type-builder, scenario-agent-builder,
  agui-verifier), `.claude/commands/`, `.claude/settings.json` (allow + deny).
- **Antigravity**: `.agents/rules/` (start/invariants/verify/isolation/aws/
  collaboration), `.agents/workflows/`.
- **8 commands/workflows**: `/check` `/verify` `/smoke` `/run` `/build` `/add-card`
  `/new-scenario` `/aws-bootstrap`.
- `scripts/check_env.sh` (prerequisite doctor), `backend/scripts/smoke_e2e.py`
  (end-to-end SSE smoke, exit-coded).

## Rules / guardrails
- **Isolation**: packages always into venv/`node_modules` (no global installs);
  `.claude/settings.json` hard-denies global installs. AWS/external services are
  out of scope for this rule.
- **AWS**: root only at bootstrap; then the `agui-deployer` profile.
- **`.gitignore` / `.dockerignore`** hardened across all folders (env variants,
  caches; the image context is only backend/agents/agentcore).
- **Collaboration protocol**: pull + read the work log before a task; verify → log
  → push after (canonical in `resources/HANDOFF.md` §11).

## Documentation
`README.md` (comprehensive), `AGENTS.md`, `CLAUDE.md`, `TODO.md`, `docs/FINDINGS.md`,
`docs/PROJECT_STATUS_AND_ROADMAP.md`, `docs/sample_run_log.jsonl`,
`resources/HANDOFF.md`, this `CHANGELOG.md`. Docs are kept in sync with each other
and with the code (cross-references checked). All docs, code, and comments are in
English.

## Remaining (TODO)
LLM tool-calling (#7 — vendor layer ready), Entra sign-in (#9), AgentCore/EKS
deploy (#10 — `/aws-bootstrap` first), CopilotKit browser verification (#4/#5),
durable HITL + replay (#11).
