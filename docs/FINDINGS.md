# Findings

Short notes captured while building Phase 1, as requested in the plan's hand-back.

## Marketplace streaming

The Marketplace gateway is treated as an OpenAI-compatible chat completions
endpoint and is the one hard external dependency. The client in
`backend/app/llm/marketplace.py` supports two modes selected by
`MARKETPLACE_STREAM_MODE`:

- `stream`, consumes the gateway `text/event-stream` and yields `delta.content`
  chunks as they arrive.
- `chunked`, requests a non-streaming completion and yields it word by word so
  the UI still animates. This is the documented fallback for when the gateway
  cannot stream.

The active mode is logged at call time (`marketplace_call`), so a run's log
shows which path was used. Because the demo ships with `AGENT_MODE=mock` by
default, the four capabilities are fully demonstrable without gateway
credentials; switch to `langgraph` once real credentials are set.

## AgentCore fit

The agent and the translator are written so the same code runs locally and on
AgentCore. `deploy/agentcore/agentcore_app.py` reuses `build_agent` and
`Translator` behind the AgentCore runtime contract (`GET /ping`,
`POST /invocations`, streaming `text/event-stream` on port 8080). The AG-UI
event stream is identical in both places, so the frontend only needs its
endpoint target changed (isolated to `lib/agui.ts`). If AgentCore's native
AG-UI shape ever diverges from the agent, the fronting FastAPI endpoint stays in
place, as the plan's risk note anticipates.

## AG-UI client, custom and CopilotKit (both shipped)

The repo now ships **two interchangeable AG-UI clients**, selected by
`NEXT_PUBLIC_CLIENT`:

- `custom` (default): a small, self-contained AG-UI-over-SSE client in
  `lib/agui.ts` with hand-built cards and a live Event Inspector. Human-in-the-loop
  and canvas work end to end here.
- `copilotkit`: the CopilotKit provider + `CopilotChat`, every card defined
  through `useCopilotAction` in `components/copilot/CopilotGenerativeUI.tsx`, a
  `/api/copilotkit` runtime route bridging to the backend via an AG-UI
  `HttpAgent`, the canvas via `useCoAgent`, scenario selection via provider
  `properties`, and the approval bridged to `/agui/resume`.

The custom client was built first (and is the default) for two reasons:

1. The human-in-the-loop design here is a single suspended run resumed through
   `POST /agui/resume` and an in-memory `asyncio.Event`, which does not match
   CopilotKit's native multi-run HITL. The custom client makes the resume flow
   exact and observable end to end.
2. It keeps a self-contained, fully verifiable path (`tsc` + `next build` pass)
   independent of a specific CopilotKit version.

The CopilotKit path is build-verified (`tsc` + `next build`); full runtime
behavior (HITL round-trip, canvas) needs a browser, which was unavailable here.
Notes: CopilotKit 1.4.x ships source-only (no `dist`) so it was upgraded to
1.62.2, which needs `npm install --legacy-peer-deps`. MSAL is declared for the
Entra work (not yet wired). All AG-UI wiring stays isolated, so pointing at
AgentCore's native endpoint later is a contained change.

## What worked

- The AG-UI Python SDK (`ag_ui.core` + `ag_ui.encoder`) mapped cleanly to a
  single-source translator. One consistent message id per text run and the
  `START, ARGS, END, RESULT` tool sequence are enforced in one place.
- Driving the agent as an async generator and passing the approval decision back
  through `asend` keeps the agent framework-pure while the translator remains
  the only event emitter.
- One run drives streaming text, a tool card, two live canvas edits, and an
  approval, and the captured log lints clean (see `sample_run_log.jsonl`).

## What surprised

- A decision posted to `/agui/resume` can arrive before the run reaches its
  suspend point. The resume registry was made order-independent (the decision is
  buffered) so the race cannot deadlock the run.
- `structlog` reserves the first positional as the event name, so the per-event
  log field had to be named `event_type` rather than `event`.
- SSE keepalives must not cancel the agent. The keepalive wrapper pumps the
  translator in a background task and only times out the queue read, so a long
  human-in-the-loop pause keeps the connection warm without interrupting the run.
