# AGENTS.md

Canonical agent guidance for this repository. It is the cross-tool standard file
(read by Google Antigravity, Claude Code, and other agentic tools). `CLAUDE.md`
imports this file; Antigravity also reads `.agents/rules/` and runs
`.agents/workflows/`. Keep this file as the single source of truth — do not
duplicate its content elsewhere; point to it.

For deep context (decision log, architecture, step-by-step plans) read
`resources/HANDOFF.md`.

## What this is

An AG-UI protocol demo: a FastAPI + LangGraph backend streams typed AG-UI events
over SSE; a Next.js frontend renders them with two interchangeable clients
(custom and CopilotKit). Full guide in `README.md`.

Working branch is `main` (everything current there). Remaining work is in
`TODO.md`; the per-item implementation plan is in `resources/HANDOFF.md` §9.

## Commands

```bash
# Backend (from backend/, venv active)
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000     # run
pytest -q                                      # unit tests (translator, HITL, lint)
python scripts/smoke_e2e.py                    # end-to-end SSE smoke, exits non-zero on failure

# Frontend (from frontend/)
npm install --legacy-peer-deps                 # CopilotKit needs --legacy-peer-deps
npm run dev                                     # run on :3000
npm run typecheck && npm run lint && npm run build
```

## Architecture invariants (do not break)

1. **One event source.** Only `backend/app/agui/translator.py` emits AG-UI
   protocol events. Agents yield semantic events (`app/agent/events.py`); the
   translator maps them and enforces ordering/pairing and HITL suspend/resume.
2. **One model path.** Every model call goes through `app/llm/` via
   `build_llm(settings)`. The provider is vendor-agnostic and selected by
   `LLM_PROVIDER` (marketplace, openai, anthropic/Claude, gemini); all expose the
   same `stream_completion(messages)` interface, so agents never depend on a
   vendor.
3. **Shared tool contract.** `backend/app/agui/catalog.py` and
   `frontend/lib/catalog.ts` must declare the same tool names and schemas
   (`scripts/smoke_e2e.py` checks parity).
4. **Identity from the bearer**, never from `RunAgentInput`.
5. **Agents stay pure.** They receive the approval decision via generator
   `asend`; they never import the translator or emit protocol events.

## Two AG-UI clients

`NEXT_PUBLIC_CLIENT` selects the frontend client:
- `custom` (default): `lib/agui.ts` SSE client, Zustand store, hand-built cards,
  live Event Inspector. HITL and canvas work end to end.
- `copilotkit`: CopilotKit provider + `CopilotChat`, cards via `useCopilotAction`
  in `components/copilot/CopilotGenerativeUI.tsx`, `/api/copilotkit` runtime route
  bridging to the backend via an AG-UI `HttpAgent`. Build-verified; full runtime
  behavior needs a browser.

## Where things live

- **Add a card/message type:** `catalog.py` + `catalog.ts`, emit it from an agent,
  handle its name in `frontend/lib/store.ts` (`handleEvent`), add a component under
  `frontend/components/catalog/`, add a `useCopilotAction` render in
  `frontend/components/copilot/CopilotGenerativeUI.tsx`, add any CSS in
  `frontend/app/globals.css`. Copy an existing card (chart/table/citations).
- **Add a scenario agent:** a class in `agents/<name>.py` implementing
  `run(input)`, register in `agents/registry.py`. It appears in the sidebar and
  is routed by `forwardedProps.agentId`.
- **Backend routing by selected agent:** `app/agent/factory.py::build_agent`.

There are eight catalog tools and ten message/card types (text and canvas are not
tools): text, lookup tool, table, chart, follow-up, suggested questions,
citations, form, approval (HITL), canvas.

## Gotchas

- `agents/` must be importable; `factory.ensure_agents_on_path()` handles it.
  Docker images build from the repo root so `agents/` is copied in.
- structlog reserves `event`; use `event_type` as the log kwarg.
- HITL resume can arrive before the run suspends; `resume.py` buffers the decision
  — keep it order-independent.
- CopilotKit 1.4.x ships source-only (no `dist`, broken); use 1.62.x with
  `--legacy-peer-deps`.

## Conventions

- **Never install anything globally.** Always use an isolated environment: a
  Python virtualenv (`backend/.venv`) for Python packages, the project-local
  `frontend/node_modules` for npm packages, and Docker for services (Postgres).
  Never install language packages globally: no `npm install -g`, no `pip install
  --user`, no `sudo pip`/`sudo npm`. If the venv or `node_modules` does not exist,
  create it first (`python -m venv backend/.venv` / `npm install
  --legacy-peer-deps`). This is about package installs only — connecting to
  external services (AWS, the Marketplace gateway, GitHub) is unaffected.
- Keep comments minimal; no comment on the same line as code; English only in code.
- Read config from env via the single `Settings` object; never hardcode.
- After any change, verify: `pytest -q` + `scripts/smoke_e2e.py` (backend) and
  `npm run typecheck && npm run lint && npm run build` (frontend). The smoke exits
  non-zero on failure.
- Work on `main`; commit and push only when asked — except the work-log entry,
  which the collaboration protocol requires you to commit and push after each task.

## Tool-specific setup

- **Claude Code:** `CLAUDE.md` (imports this file), `.claude/agents/` subagents
  (`card-type-builder`, `scenario-agent-builder`, `agui-verifier`),
  `.claude/commands/` (`/check`, `/verify`, `/smoke`, `/run`, `/build`,
  `/add-card`, `/new-scenario`, `/aws-bootstrap`).
- **Antigravity:** this `AGENTS.md`, always-on rules in `.agents/rules/`, and
  slash workflows in `.agents/workflows/` (`/check`, `/verify`, `/smoke`, `/run`,
  `/build`, `/add-card`, `/new-scenario`, `/aws-bootstrap`). Note: some
  Antigravity versions read `.agent/workflows/` (singular). If a workflow is
  ignored, rename the folder to match your version.

`/check` verifies prerequisites; `/run` starts the dev servers; `/build` builds
the Docker images; `/aws-bootstrap` sets up the scoped AWS deployer.

## AWS

Bootstrap AWS once with root to create a scoped IAM user, then always use that
user (`--profile agui-deployer`), never root. Flow, policy, and script are in
`deploy/aws/` (see `.agents/rules/40-aws.md`). Connecting to AWS is not
restricted by the install-isolation rule.

## Collaboration protocol (multiple agents / tools)

More than one agent may work `main` in parallel (Claude Code, Antigravity, …).
**Before a task:** `git pull`, review changes, and read the newest entries in the
work log at the end of `resources/HANDOFF.md`. **After a task:** run the standard
verification and, only if green, prepend a short work-log entry (identity, what
you did, what you plan next) and push to `main` — this is the one exception to
"push only when asked". The full steps, conflict handling, and entry format are
the **canonical copy** in that work log; follow it there.
