# AG-UI Demo

A small, Claude-like AI assistant workspace built to exercise the **AG-UI
protocol** end to end. AG-UI (Agent-User Interaction Protocol) is an open,
event-based protocol: the backend streams typed JSON events (lifecycle, text,
tool calls, state, custom) to the frontend over Server-Sent Events, and the
frontend renders each one. This repository is a full, runnable reference: a
FastAPI + LangGraph backend, a Next.js frontend with **two interchangeable
AG-UI clients**, scenario agents, and prepared cloud-deploy assets.

---

## Table of contents

1. [What it does](#what-it-does)
2. [What tasks it performs](#what-tasks-it-performs)
3. [Architecture](#architecture)
4. [Repository layout](#repository-layout)
5. [Prerequisites](#prerequisites)
6. [Setup and install](#setup-and-install)
7. [Running it](#running-it)
8. [Demo walkthrough](#demo-walkthrough)
9. [The two AG-UI clients](#the-two-ag-ui-clients)
10. [Message types and generative UI](#message-types-and-generative-ui)
11. [Scenario agents](#scenario-agents)
12. [HTTP API](#http-api)
13. [Configuration reference](#configuration-reference)
14. [Testing and verification](#testing-and-verification)
15. [Event logs and evidence](#event-logs-and-evidence)
16. [Cloud deployment](#cloud-deployment)
17. [Troubleshooting](#troubleshooting)
18. [Roadmap and status](#roadmap-and-status)

---

## What it does

The demo is a two-region workspace, like a modern assistant:

- **Left sidebar** — a list of selectable **agents** (top) and the signed-in
  user's **conversation history** (below).
- **Right** — the **chat area**, with streamed assistant messages, tool cards,
  a **document canvas** that opens beside the chat when the agent edits a
  document, and **approval cards** when the agent needs a decision.

It demonstrates, live, the four AG-UI capabilities plus more card types:

- **Streaming chat** — tokens appear as the model produces them.
- **A visible tool call** — rendered as a live card.
- **A shared-state document canvas** — the agent edits it live while it talks.
- **A human-in-the-loop approval** — the agent pauses and resumes on your answer.
- **Extra message types** — tables, follow-up lists, and suggested questions.

Everything runs locally with no external credentials by default (a scripted
`mock` agent drives all capabilities). Point it at a real model and cloud when
you are ready.

## What tasks it performs

- Accepts a user message, runs an agent, and **streams typed AG-UI events** back
  over SSE.
- **Looks facts up** with a backend tool and renders the result as a card.
- **Drafts and edits a shared document** on a Tiptap canvas via JSON Patch state
  deltas, live, while chat is still streaming.
- **Renders structured outputs** — tables, follow-up/next-step lists, and
  suggested-question chips.
- **Pauses for human approval** and resumes the same run on the decision.
- **Persists conversations** to PostgreSQL and reloads history per user.
- **Captures every run's event stream** to a JSONL log that can be pulled,
  ordering-linted, and replayed.
- Routes between **scenario-specific agents** (research, writing, analytics,
  support), each showcasing a different mix of the above.

## Architecture

```
frontend (Next.js, React, TS)                backend (FastAPI)
  lib/agui.ts     custom AG-UI/SSE client       api/agui_router.py   POST /agui/run (SSE), /agui/resume
  lib/store.ts    event reducer -> UI            agui/translator.py   the ONLY place AG-UI events are emitted
  components/                                    agui/catalog.py      frontend-tool schemas (shared contract)
    chat, catalog, canvas, inspector            agent/factory.py     picks mock | langgraph | scenario
  components/copilot/                            agent/graph.py       LangGraph agent (streams via Marketplace)
    CopilotChat + useCopilotAction cards         agent/mock.py        scripted showcase agent
  app/api/copilotkit/route.ts                    agents/ (top level)  scenario agents
    CopilotKit runtime -> HttpAgent -> backend   llm/marketplace.py   streaming gateway client
                                                 db/*                 PostgreSQL history, swappable repo
                                                 auth/entra.py        dev stub | Entra bearer validation
```

Key invariants:

- **One event source.** Only `app/agui/translator.py` emits AG-UI protocol
  events. Agents yield framework-neutral *semantic* events; the translator maps
  them and enforces ordering, pairing, and the human-in-the-loop suspend/resume.
- **One model path.** Every model call goes through `app/llm/marketplace.py`.
- **Shared tool contract.** The frontend declares the tools it can render in
  `RunAgentInput.tools` (`frontend/lib/catalog.ts`); the backend advertises the
  same schemas (`backend/app/agui/catalog.py`); the agent calls them by name.
- **Identity from the bearer**, never from `RunAgentInput`.

## Repository layout

```
aguiDemo/
  README.md                     this file
  .env.example                  every config value, documented
  docker-compose.yml            local Postgres
  TODO.md                       remaining work
  backend/                      FastAPI + LangGraph backend
    app/
      main.py                   app, CORS, routers, lifespan
      config/settings.py        pydantic-settings, env-driven
      api/                      agui_router, conversations, agents
      agui/                     translator, catalog, resume, lint, run_capture
      agent/                    graph (LangGraph), mock, tools, factory, events
      llm/marketplace.py        streaming gateway client
      db/                       models, session, repository
      auth/entra.py             bearer validation dependency
      logging/setup.py          structlog config
    tests/test_event_order.py   ordering-lint tests
  frontend/                     Next.js App Router frontend
    app/                        layout, page, providers, api/copilotkit route
    components/                 sidebar, chat, catalog, canvas, inspector, copilot
    lib/                        agui, store, api, catalog, auth
  agents/                       scenario agents (separate package)
  deploy/agentcore/             Phase 2, AgentCore packaging + Dockerfile
  deploy/eks/                   Phase 3, Helm chart
  docs/                         FINDINGS, PROJECT_STATUS_AND_ROADMAP, sample log
```

## Prerequisites

- **Python 3.11**
- **Node 20+** and npm
- **Docker** (for the local Postgres container)

## Setup and install

### 1. Environment

```bash
cp .env.example .env
```

The defaults (`AGENT_MODE=mock`, `AUTH_MODE=dev`, `NEXT_PUBLIC_CLIENT=custom`)
run the whole demo with no external credentials. Fill in `MARKETPLACE_*` and set
`AGENT_MODE=langgraph` only when you want a real model.

### 2. Local Postgres

```bash
docker compose up -d postgres
```

History persistence degrades gracefully if Postgres is absent (runs still
stream), but the sidebar history needs it.

### 3. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### 4. Frontend

```bash
cd frontend
npm install
```

> If npm reports a peer-dependency conflict from the CopilotKit packages, use
> `npm install --legacy-peer-deps`.

## Running it

Two terminals:

```bash
# terminal 1, backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
# health check:
curl localhost:8000/health

# terminal 2, frontend
cd frontend
npm run dev            # http://localhost:3000
```

## Demo walkthrough

Open http://localhost:3000 and try:

> explain ag-ui, compare the types, next steps, draft a note then approve

You will see, in one run: streaming text, a `lookupKnowledge` tool card, a
**table**, a **follow-up** list, **suggested-question** chips, the **canvas**
opening and filling live, and an **approval** card. Approve or reject to resume
the run.

Pick a different **agent** in the sidebar (Research Assistant, Doc Writer, Data
Analyst, Support Triage) to see different card combinations. Click **Show
events** (top bar, custom client) to watch the raw AG-UI stream live.

## The two AG-UI clients

`NEXT_PUBLIC_CLIENT` selects the frontend client without touching the backend:

| Mode | What it uses | Notes |
| --- | --- | --- |
| `custom` (default) | Hand-built AG-UI/SSE client in `lib/agui.ts`, Zustand store, hand-built cards, and a live **Event Inspector** | Human-in-the-loop works end to end via `/agui/resume` |
| `copilotkit` | CopilotKit provider + `CopilotChat`, cards via `useCopilotAction`, `/api/copilotkit` runtime route bridging to the backend with an AG-UI `HttpAgent`. Canvas via `useCoAgent`, scenario selection via provider `properties`, approval bridged to `/agui/resume` | Build-verified; full runtime behavior needs a browser |

All AG-UI wiring is isolated (custom: `lib/agui.ts`; CopilotKit:
`components/copilot/` + `app/api/copilotkit/route.ts`), so the endpoint target
can later point at AgentCore's native AG-UI endpoint with a one-file change.

## Message types and generative UI

The agent sends different message types over AG-UI and each maps to a component:

| Message type | AG-UI representation | Custom client | CopilotKit client |
| --- | --- | --- | --- |
| Streaming text | `TEXT_MESSAGE_*` | chat bubble | `CopilotChat` |
| Backend lookup | `lookupKnowledge` call + result | `ToolCard` | `useCopilotAction` render |
| Table | `renderTable` call | `TableCard` | `useCopilotAction` render |
| Chart | `renderChart` call | `ChartCard` (SVG bars) | `useCopilotAction` render |
| Follow-up / next steps | `renderFollowUp` call | `FollowUpCard` | `useCopilotAction` render |
| Suggested questions | `renderSuggestedQuestions` call | chips | `useCopilotAction` render |
| Citations / sources | `renderCitations` call | `CitationsCard` | `useCopilotAction` render |
| Form (structured input) | `renderForm` call | `FormCard` | `renderAndWaitForResponse` |
| Approval (HITL) | `requestApproval` + `/agui/resume` | `ApprovalCard` | `renderAndWaitForResponse` |
| Canvas edits | `STATE_SNAPSHOT` / `STATE_DELTA` | Tiptap canvas | (roadmap: `useCoAgent`) |

Adding a new card type: declare a tool in both catalogs, handle its name in the
store reducer (custom) and add a `useCopilotAction` render (CopilotKit), then
add a component.

## Scenario agents

`agents/` is a separate package of scenario-specific agents. Each is a scripted
agent (no credentials needed) showcasing a distinct mix of card types:

| Agent id | Focus | Card types |
| --- | --- | --- |
| `research-assistant` | Look a topic up, compare sources | text, lookup, table, suggestions |
| `doc-writer` | Draft on the canvas, ask to finalize | text, canvas, follow-up, approval |
| `data-analyst` | Metrics table and insights | text, table, follow-up, suggestions |
| `support-triage` | Find an answer, escalate on approval | text, lookup, approval, follow-up |

They appear in the sidebar; the frontend sends the selected id in
`RunAgentInput.forwardedProps`, and `app/agent/factory.py` routes to the agent.
Because they reuse the translator, they are AgentCore-deployable unchanged. See
`agents/README.md`.

## HTTP API

- `POST /agui/run` — body is `RunAgentInput`; response is the AG-UI event stream
  (`text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`,
  keepalive every 15s). Persists the user turn and assistant result.
- `POST /agui/resume` — resolves a suspended run with the approval decision.
- `GET /agui/runs/{run_id}/log` — pulls the captured event log for a run.
- `GET /conversations`, `GET /conversations/{id}`, `POST /conversations`.
- `GET /agents` — the selectable agent list for the sidebar.
- `GET /health` — liveness plus the active agent and auth modes.
- `POST /api/copilotkit` (frontend) — CopilotKit runtime endpoint bridging to the
  backend.

## Configuration reference

See `.env.example` for the full, commented list. Highlights:

| Variable | Meaning |
| --- | --- |
| `AGENT_MODE` | `mock` (scripted) or `langgraph` (real model) |
| `AUTH_MODE` | `dev` (stub identity) or `entra` (validate Entra bearer) |
| `MARKETPLACE_*` | Gateway URL, key, model, `stream`/`chunked` mode |
| `DATABASE_URL` | async Postgres connection string |
| `NEXT_PUBLIC_BACKEND_URL` | where the frontend sends AG-UI runs |
| `NEXT_PUBLIC_CLIENT` | `custom` or `copilotkit` |
| `BACKEND_URL` | server-side URL the CopilotKit runtime route calls |
| `NEXT_PUBLIC_AUTH_MODE` | `dev` or `entra` for the frontend |

## Testing and verification

```bash
# backend, translator + HITL + ordering-lint tests
cd backend && source .venv/bin/activate && pytest -q

# backend, end-to-end SSE smoke (health, every scenario streamed with resolved
# HITL, ordering-lint, run-log, catalog parity), exits non-zero on failure
cd backend && source .venv/bin/activate && python scripts/smoke_e2e.py

# frontend, typecheck, lint, production build
cd frontend && npm run typecheck && npm run lint && npm run build
```

Working in a local Claude Code session? `CLAUDE.md` and `.claude/` provide
project memory, the `/verify` and `/smoke` commands, and subagents for adding
card types and scenario agents.

## Event logs and evidence

Each run writes one JSON line per AG-UI event to
`backend/run_logs/<run_id>.jsonl` with `run_id`, `thread_id`, and `user`. The
ordering lint lives in `app/agui/lint.py` and is exercised by
`tests/test_event_order.py`. A captured, lint-clean sample is checked in at
`docs/sample_run_log.jsonl`.

## Cloud deployment

Prepared for later, manual runs:

- **Phase 2, AgentCore** — `deploy/agentcore/` packages the same agent behind the
  AgentCore runtime contract, Dockerfile supporting both the CLI and the
  ECR-then-register paths.
- **Phase 3, EKS** — `deploy/eks/` is a minimal Helm chart for frontend and
  backend, RDS via env, Entra required.

Each has its own `README.md` with step-by-step commands.

## Troubleshooting

- **Sidebar history is empty** — Postgres is not running; `docker compose up -d
  postgres`. Runs still stream without it.
- **No streamed answer with a real model** — check `MARKETPLACE_*` and set
  `AGENT_MODE=langgraph`; the active stream mode is logged as `marketplace_call`.
- **CopilotKit npm install fails** — use `npm install --legacy-peer-deps`.
- **SSE looks buffered behind a proxy** — the backend sets `X-Accel-Buffering:
  no`; confirm the proxy or load balancer does not buffer `text/event-stream`.
- **CORS errors** — set `CORS_ALLOW_ORIGINS` to the frontend origin.

## Roadmap and status

`TODO.md` lists the remaining work. `docs/PROJECT_STATUS_AND_ROADMAP.md` covers
what is done, which CopilotKit primitives fit which message type, and next
steps. `docs/FINDINGS.md` records the Marketplace streaming, AgentCore fit, and
CopilotKit decisions, and what surprised us.
