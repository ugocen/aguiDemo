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

## AG-UI client, CopilotKit vs the fallback

The plan names CopilotKit as the primary AG-UI client and `@ag-ui/client` with a
hand-built pane as the sanctioned fallback. This build uses the fallback path:
`lib/agui.ts` is a small, self-contained AG-UI-over-SSE client and the four
catalog components are hand-built. Two reasons drove this:

1. The human-in-the-loop design here is a single suspended run resumed through
   `POST /agui/resume` and an in-memory `asyncio.Event`, which does not match
   CopilotKit's native multi-run HITL. The custom client makes the resume flow
   exact and observable.
2. It keeps the frontend self-contained and verifiable (`tsc` and `next build`
   both pass) without depending on a specific CopilotKit version.

All AG-UI wiring is isolated to `lib/agui.ts`, so swapping to CopilotKit's
`HttpAgent` or AgentCore's native endpoint is a one-module change, exactly as
the plan requires. CopilotKit and MSAL remain declared in `package.json` as the
intended stack.

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
