# CLAUDE.md

Project guidance for Claude Code working in this repository. For deep context
(decision log, roadmap, step-by-step plans) read `resources/HANDOFF.md` first.

## What this is

An AG-UI protocol demo: a FastAPI + LangGraph backend streams typed AG-UI events
over SSE; a Next.js frontend renders them with two interchangeable clients
(custom and CopilotKit). See `README.md` for the full guide.

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

- **One event source.** Only `backend/app/agui/translator.py` emits AG-UI
  protocol events. Agents yield semantic events (`app/agent/events.py`); the
  translator maps them and enforces ordering/pairing.
- **One model path.** Every model call goes through `app/llm/marketplace.py`.
- **Shared tool contract.** `backend/app/agui/catalog.py` and
  `frontend/lib/catalog.ts` must declare the same tool names and schemas.
- **Identity from the bearer**, never from `RunAgentInput`.
- **Agents stay pure.** They receive the approval decision via generator
  `asend`; they never import the translator or emit protocol events.

## Where things live

- Add a card/message type: `catalog.py` + `catalog.ts`, emit it from an agent,
  handle it in `frontend/lib/store.ts` (`handleEvent`), add a component under
  `frontend/components/catalog/`, and a `useCopilotAction` render in
  `frontend/components/copilot/CopilotGenerativeUI.tsx`. Use the
  `card-type-builder` subagent.
- Add a scenario agent: a class in `agents/`, register in `agents/registry.py`.
  Use the `scenario-agent-builder` subagent.
- Backend routing by selected agent: `app/agent/factory.py::build_agent`.

## Gotchas

- `agents/` must be importable; `factory.ensure_agents_on_path()` handles it.
  Docker images build from the repo root so `agents/` is copied in.
- structlog reserves `event`; use `event_type` as the log kwarg.
- HITL resume can arrive before the run suspends; `resume.py` buffers it — keep
  it order-independent.
- CopilotKit 1.4.x ships source-only (broken); use 1.62.x with
  `--legacy-peer-deps`.

## Conventions

- Keep comments minimal; no comment on the same line as code; English only.
- Read config from env via the single `Settings` object; never hardcode.
- After changes, run `pytest -q` + `scripts/smoke_e2e.py` (backend) and
  `typecheck`/`lint`/`build` (frontend). Prefer the `/verify` command.

## Status

Working branch is `main`. Remaining work is in `TODO.md`; the implementation plan
per item is in `resources/HANDOFF.md` section 9.
