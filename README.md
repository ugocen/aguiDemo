# AG-UI Demo

A small assistant workspace that exercises the [AG-UI protocol](https://docs.ag-ui.com):
the backend streams typed JSON events (lifecycle, text, tool calls, state,
custom) to the frontend over Server-Sent Events, and the frontend renders them.

Four capabilities are demonstrated live in one signed-in session:

- **Streaming chat**, tokens appear as the model produces them.
- **A visible tool call**, rendered as a live card.
- **A shared-state document canvas**, the agent edits it live while it talks.
- **A human-in-the-loop approval**, the agent pauses and resumes on your answer.

Phase 1 runs entirely on a local machine. AgentCore and EKS assets are prepared
for later, manual deploys (see `deploy/`).

## Architecture

```
frontend (Next.js, React, TS)  --AG-UI over SSE-->  backend (FastAPI)
  lib/agui.ts   single client                         api/agui_router.py  SSE + resume
  lib/store.ts  event reducer                         agui/translator.py  single event source
  Tiptap canvas, catalog cards                        agent/graph.py      LangGraph agent
                                                       agent/mock.py       scripted agent
                                                       llm/marketplace.py  gateway client
                                                       db/*                Postgres history
```

- Every model call routes through `backend/app/llm/marketplace.py`.
- Every AG-UI event is emitted from one module, `backend/app/agui/translator.py`.
- Config is env-driven through one `Settings` object; nothing is hardcoded.
- Identity comes from the bearer, never from `RunAgentInput`.

## Prerequisites

- Python 3.11, Node 20+, Docker (for local Postgres).

## Setup

```bash
cp .env.example .env
```

The defaults run with `AGENT_MODE=mock` and `AUTH_MODE=dev`, so the whole demo
works without gateway credentials or sign-in. Set `MARKETPLACE_*` and switch
`AGENT_MODE=langgraph` to stream from a real model.

### 1. Local Postgres

```bash
docker compose up -d postgres
```

History persistence degrades gracefully if Postgres is absent (runs still
stream), but the sidebar history needs it.

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Health check: `curl localhost:8000/health`.

Run the event-order tests:

```bash
cd backend && source .venv/bin/activate && pytest -q
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Try:

> explain ag-ui and draft a note then approve

You will see streaming text, a `lookupKnowledge` tool card, the canvas panel
opening and filling live, and an approval card. Approve or reject to resume.

## Environment variables

See `.env.example` for the full list. Key ones:

| Variable | Meaning |
| --- | --- |
| `AGENT_MODE` | `mock` (scripted, no external calls) or `langgraph` (real model) |
| `AUTH_MODE` | `dev` (stub identity) or `entra` (validate Entra bearer) |
| `MARKETPLACE_*` | GenAI Marketplace gateway URL, key, model, stream mode |
| `DATABASE_URL` | async Postgres connection string |
| `NEXT_PUBLIC_BACKEND_URL` | where the frontend sends AG-UI runs |
| `NEXT_PUBLIC_AUTH_MODE` | `dev` or `entra` for the frontend |

## Endpoints

- `POST /agui/run`, body is `RunAgentInput`, response is the AG-UI event stream
  (`text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`,
  keepalive every 15s). Persists the user turn and assistant result.
- `POST /agui/resume`, resolves a suspended run with the approval decision.
- `GET /agui/runs/{run_id}/log`, pulls the captured event log for a run.
- `GET /conversations`, `GET /conversations/{id}`, `POST /conversations`.
- `GET /agents`, the callable agent list for the sidebar.

## Sign-in

Phase 1 defaults to a dev stub identity. To require Microsoft Entra sign-in, set
`AUTH_MODE=entra` (backend validates the bearer against the tenant JWKS) and
`NEXT_PUBLIC_AUTH_MODE=entra`, then wire the MSAL token acquisition in
`frontend/lib/auth.ts` (the stub returns a placeholder today). History and runs
are scoped to the signed-in user in both modes.

## Demo-scope simplifications

- **In-memory resume.** Human-in-the-loop suspension uses a per-run
  `asyncio.Event` keyed by `run_id` (`backend/app/agui/resume.py`). A production
  system would back this with a durable workflow engine so a suspended run
  survives a restart. **Temporal is intentionally not used here.**
- **Marketplace gateway** is assumed OpenAI-compatible; a chunked fallback ships
  for when streaming is unavailable.
- The demo knowledge base and the LangGraph plan heuristics are intentionally
  tiny, one tool and one document capability.

## Event logs and evidence (M6)

Each run writes one JSON line per AG-UI event to `backend/run_logs/<run_id>.jsonl`
with `run_id`, `thread_id`, and `user`, so a run can be pulled, linted, and
replayed. The ordering lint lives in `backend/app/agui/lint.py` and is exercised
by `backend/tests/test_event_order.py`. A captured, lint-clean sample is checked
in at `docs/sample_run_log.jsonl`.

## Cloud phases (prepared, deployed manually later)

- **Phase 2, AgentCore**: `deploy/agentcore/` packages the same agent behind the
  AgentCore runtime contract, with a Dockerfile supporting both the AgentCore
  CLI and the ECR-then-register paths.
- **Phase 3, EKS**: `deploy/eks/` is a minimal Helm chart for frontend and
  backend, RDS via env, Entra required.

Both are described step by step in their own `README.md`. This repository
prepares everything those phases need but does not perform the cloud deploys.

## Findings

See `docs/FINDINGS.md` for the Marketplace streaming answer, the AgentCore fit
answer, the CopilotKit decision, and what worked / what surprised.
