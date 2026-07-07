# TODO

Remaining work, roughly in priority order. Done items are in the git history and
summarized in `docs/PROJECT_STATUS_AND_ROADMAP.md`.

## Done

- [x] Backend: FastAPI + LangGraph, single-source translator, SSE + keepalive.
- [x] Human-in-the-loop suspend/resume (in-memory), event capture + ordering lint.
- [x] Frontend: two-region workspace, custom AG-UI/SSE client, Zustand store.
- [x] Message types: text, tool card, table, follow-up, suggested questions,
      approval, canvas. Live Event Inspector.
- [x] Second client: CopilotKit provider + CopilotChat + `useCopilotAction`
      cards, `/api/copilotkit` runtime route (build-verified).
- [x] Scenario agents in `agents/`, each mapped to a canonical AG-UI Dojo
      feature (research-desk, trip-architect, incident-commander, growth-analyst,
      content-studio), routed by selected agent id.
- [x] Domain scenarios with new card types and bidirectional **Shared State**:
      travel-concierge (OTA: hotels + date picker + booking cart), platform-architect
      (air-gapped DevOps: command output + AsciiDoc Docs-as-Code canvas), math-coach
      (adaptive mental-math quiz). Adds `renderHotels`/`renderDatePicker`/
      `renderCommandOutput`/`renderQuiz` and a `sharedState` channel that round-trips
      UI selections back to the agent (`StateDelta` + `RunAgentInput.state`).
- [x] Cloud assets prepared: AgentCore packaging, EKS Helm chart, Dockerfiles.
- [x] Docs: README, FINDINGS, PROJECT_STATUS_AND_ROADMAP, sample event log.

## Next (code, verifiable locally)

- [x] **Chart/metrics card type** — `renderChart` in both catalogs, inline SVG
      bar chart (custom) + `useCopilotAction` render (CopilotKit), used by the
      data-analyst scenario.
- [x] **CopilotKit-native HITL** — approval `renderAndWaitForResponse` bridges to
      `/agui/resume` (the backend injects `runId` into the approval args). Build
      verified; needs a browser to confirm the round-trip end to end.
- [x] **Canvas in CopilotKit mode** — the shared document state is read via
      `useCoAgent` and rendered by `CopilotCanvasPanel`.
- [x] **Scenario selection in CopilotKit mode** — the selected agent id is passed
      through the CopilotKit provider `properties`, forwarded to the backend.
- [x] **More card types** — citations/sources list and a form (structured input).
      Citations render-only; form submits collected values back (custom: as the
      next user turn; CopilotKit: via renderAndWaitForResponse).

## Later (needs credentials or is manual)

- [x] **Real LLM tool-calling** — the model now *decides* which card to render
      via function calling (vendor-agnostic `stream_chat` on every provider →
      `LLMToolAgent`'s bounded tool-use loop: render cards, `lookupKnowledge`,
      and HITL `requestApproval`). In `langgraph` mode with a provider key the
      default agent and the research-desk / trip-architect / incident-commander /
      growth-analyst scenarios are model-driven; `content-studio` stays scripted
      (the canvas has no tool), and `mock` mode / no key stay scripted so the demo
      and smoke are deterministic.
    - [ ] Optional: an `editDocument` tool so the canvas (content-studio) is
          model-driven too; expose the default LLM agent in the sidebar.
- [ ] **Entra sign-in end to end** — MSAL token in `frontend/lib/auth.ts`,
      `AUTH_MODE=entra`, per-user scoping (needs Entra app registration).
- [ ] **AgentCore deploy** (Phase 2) and **EKS deploy** (Phase 3) — run the
      prepared manual steps (needs AWS). First run `/aws-bootstrap` once with root
      to create the scoped `agui-deployer` IAM user, then deploy with that profile
      (`deploy/aws/`).
- [ ] **Durable HITL** — replace the in-memory resume registry with a
      workflow-backed store so suspended runs survive restarts.
- [ ] **Replay dashboard** — pull, lint, and replay captured event logs in the UI.

The canonical, live version of this list is the session task tracker; this file
mirrors it for anyone reading the repo.
