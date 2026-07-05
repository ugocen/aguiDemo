# AG-UI Demo — Status and Roadmap

This document answers three questions: **(1) what we have built so far, (2) which
CopilotKit card/message primitives apply and which we have ready, (3) what we can
do next.**

---

## 1. What we have built so far

### Backend (FastAPI + LangGraph + `ag-ui-protocol`)
- **Single-source translator** (`app/agui/translator.py`): all AG-UI events are
  emitted from one place. Run lifecycle pairing, one `messageId` per text message,
  the `TOOL_CALL_START/ARGS/END/RESULT` sequence, `STATE_SNAPSHOT/DELTA` for the
  canvas, and human-in-the-loop suspend/resume are enforced in one spot.
- **Agents**: `mock` (scripted, no credentials needed) and `langgraph` (real model
  via a provider). Both produce semantic events; the approval decision returns
  through the generator `asend` channel, so the agent stays framework-neutral.
- **Model path** (`app/llm/`): vendor-agnostic, selected by `LLM_PROVIDER`
  (marketplace/openai/anthropic/gemini); `stream` and `chunked` fallback modes,
  the active mode is logged.
- **Persistence**: PostgreSQL history behind a swappable repository interface.
- **Auth**: dev stub + Microsoft Entra bearer validation.
- **HITL resume**: an in-memory `asyncio.Event` keyed by run_id (demo scope,
  Temporal deliberately not used).
- **Evidence (M6)**: per-run event-log capture + ordering lint and tests.

### Frontend (Next.js App Router, TS strict, Zustand, Tiptap)
- A Claude-like two-region workspace: **Agents + History** on the left, **chat**
  on the right, a **Tiptap canvas** that opens when the agent edits a document.
- **Two AG-UI clients**, selected by `NEXT_PUBLIC_CLIENT`:
  - `custom` (default): our own lightweight AG-UI/SSE client in `lib/agui.ts`,
    hand-built cards, and the **Event Inspector** (a live event stream).
  - `copilotkit`: CopilotKit provider + `CopilotChat` + `useCopilotAction` cards,
    connected to the AG-UI backend through the `/api/copilotkit` runtime route.
- **Message/card types (10)**: streaming text, lookup tool card, **table**,
  **chart**, **follow-up / next steps**, suggested questions, **citations**,
  **form**, approval (HITL), canvas. (8 of these are tools in the `catalog`; text
  and canvas are not tools.)

### Scenario agents (`agents/` — separate folder)
Four scripted scenario agents, each showing a different card combination:
`research-assistant`, `doc-writer`, `data-analyst`, `support-triage`. Selected
from the sidebar; the frontend sends the selected agent id via `forwardedProps`,
and the backend `build_agent` routes to the right agent. Details: `agents/README.md`.

### Cloud assets (prepared, deployed manually)
- `deploy/agentcore/`: packages the same agent behind the AgentCore runtime
  contract (`/ping`, `/invocations`); both the CLI and ECR-register paths.
- `deploy/eks/`: a minimal Helm chart for frontend + backend, RDS and Entra.

### Verification
- Backend tests pass; all four scenario agents produce a lint-clean stream.
- Frontend `tsc` and `next build` (both custom and CopilotKit) pass clean.
- End-to-end SSE run: streaming text → tool → canvas → approval suspend →
  `/agui/resume` → `RUN_FINISHED`.

---

## 2. Which CopilotKit cards/message types apply

CopilotKit has no "built-in card list"; you define the generative UI yourself. In
the version we set up (1.62.2), the available building blocks and which message
type each fits:

### Primitives that render cards/messages
| CopilotKit primitive | What it does | Which of our message types it fits |
| --- | --- | --- |
| `useCopilotAction` + `render` | Renders a tool the agent calls as a card | table, follow-up, suggested questions, lookup tool card |
| `useCopilotAction` + `renderAndWaitForResponse` | Human-in-the-loop; returns the user's answer via `respond()` | approval card |
| `useCopilotAction` + `name: "*"` | Catch-all render for any unmatched tool call | unknown/future card types |
| `useCoAgent` + `useCoAgentStateRender` | Binds and renders shared agent state | canvas / shared-state document |
| `useCopilotChatSuggestions` | Generates suggested questions for the chat | suggested questions (native path) |
| `useCopilotReadable` | Exposes app state to the agent as context | making the selected doc/agent context |
| `CopilotChat` / `CopilotSidebar` / `CopilotPopup` | Ready-made chat surfaces | the main chat area |
| `Markdown`, `ImageRenderer`, `Suggestion(s)` | Rich in-message render | text, image, suggestion chips |
| `CopilotDevConsole` | Developer console | the CopilotKit counterpart of our Event Inspector |

### Cards we have READY in CopilotKit
In `components/copilot/CopilotGenerativeUI.tsx` via `useCopilotAction`:
- `lookupKnowledge` → tool card (`render`)
- `renderTable` → table card (`render`)
- `renderFollowUp` → follow-up list (`render`)
- `renderSuggestedQuestions` → suggestion chips (`render`)
- `requestApproval` → approval card (`renderAndWaitForResponse`)

All of these share exact names with the backend catalog; the agent calls a tool by
name and CopilotKit shows the matching render inline in the chat.

### Also ready in CopilotKit mode
- **Canvas**: the shared-state document is read via `useCoAgent` and rendered live
  by `CopilotCanvasPanel`.
- **Scenario selection**: the sidebar's selected agent id passes to the backend as
  `forwardedProps` via the CopilotKit provider `properties`.
- **HITL approval**: the backend injects `runId` into the approval tool-call args;
  the CopilotKit approval card both calls `respond()` and bridges to `/agui/resume`.

### Current known limit
- CopilotKit verification was done at the **compile/bundling** level (`tsc` +
  `next build` pass). Fully verifying the HITL round-trip and the canvas's visual
  behavior needs **a browser + a running backend**; there is no browser in this
  environment. In the `custom` client, HITL and canvas already work end to end.

---

## 3. What we can do next

### Done (short term, now complete)
- ✅ **CopilotKit-native HITL bridge**: `runId` injected into the approval args;
  the CopilotKit approval card calls `respond()` + the `/agui/resume` bridge. (Full
  round-trip awaits browser verification.)
- ✅ **Bind the canvas via `useCoAgent`**: `CopilotCanvasPanel` reads shared state.
- ✅ **Scenario selection in CopilotKit mode**: the selected id passes as
  `forwardedProps` via provider `properties`.
- ✅ **New cards**: chart, citations, form (in both clients).

### Short term (remaining)
1. **Native suggestions**: move suggested questions to CopilotKit's own mechanism
   with `useCopilotChatSuggestions` (currently via a `useCopilotAction` render).
2. More generative UI cards: **file/attachment**, **code block**, **map** — use the
   `card-type-builder` subagent for the pattern.
3. Power the scenario agents with a **real LLM** (Marketplace/`langgraph`); replace
   the scripted flows with model tool-calling decisions (see HANDOFF §9 #7).

### Long term (production and cloud)
4. **AgentCore deploy** (Phase 2) and **EKS deploy** (Phase 3) — assets are ready,
   manual steps in `deploy/*/README.md`.
5. Enable **Entra sign-in** and scope history and runs to the user.
6. **Durable HITL**: a persistent workflow engine instead of the in-memory resume.
7. Observability: capture, lint, and replay event logs in a dashboard.

> The live list of remaining work is in `TODO.md`; the per-item implementation
> plan is in `resources/HANDOFF.md` §9.

---

## How to try it

```bash
# custom client (default, HITL works end to end, Event Inspector present)
cp .env.example .env
cd backend && uvicorn app.main:app --reload
cd frontend && npm install --legacy-peer-deps && npm run dev   # http://localhost:3000

# CopilotKit client
# .env: NEXT_PUBLIC_CLIENT=copilotkit

# verification (after code changes)
cd backend && python scripts/smoke_e2e.py   # end-to-end SSE smoke, exit-coded
```

For a local Claude Code session, `CLAUDE.md` + `.claude/` (subagents and the
`/verify`, `/smoke`, `/add-card`, `/new-scenario` commands) are ready.

Select a scenario agent in the sidebar (e.g. Doc Writer) and send a message; each
agent produces a different card combination. For the message-type mapping table
and the architecture, see the root `README.md` and `docs/FINDINGS.md`.
