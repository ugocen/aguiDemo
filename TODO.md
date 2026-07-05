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
- [x] Scenario agents in `agents/` (research, doc-writer, data-analyst,
      support-triage), routed by selected agent id.
- [x] Cloud assets prepared: AgentCore packaging, EKS Helm chart, Dockerfiles.
- [x] Docs: README, FINDINGS, PROJECT_STATUS_AND_ROADMAP, sample event log.

## Next (code, verifiable locally)

- [x] **Chart/metrics card type** — `renderChart` in both catalogs, inline SVG
      bar chart (custom) + `useCopilotAction` render (CopilotKit), used by the
      data-analyst scenario.
- [ ] **CopilotKit-native HITL** — make `renderAndWaitForResponse` approval work
      end to end (backend mode that ends the run and consumes the tool result on
      the next run, or bridge respond() to `/agui/resume`). Needs browser test.
- [ ] **Canvas in CopilotKit mode** — expose shared state via `useCoAgent` and
      render with `useCoAgentStateRender`.
- [ ] **Scenario selection in CopilotKit mode** — pass the selected agent id to
      the CopilotKit HttpAgent.
- [x] **More card types** — citations/sources list and a form (structured input).
      Citations render-only; form submits collected values back (custom: as the
      next user turn; CopilotKit: via renderAndWaitForResponse).

## Later (needs credentials or is manual)

- [ ] **Real LLM for scenario agents** — swap scripted flows for model decisions
      via the Marketplace/LangGraph path (needs Marketplace credentials).
- [ ] **Entra sign-in end to end** — MSAL token in `frontend/lib/auth.ts`,
      `AUTH_MODE=entra`, per-user scoping (needs Entra app registration).
- [ ] **AgentCore deploy** (Phase 2) and **EKS deploy** (Phase 3) — run the
      prepared manual steps (needs AWS).
- [ ] **Durable HITL** — replace the in-memory resume registry with a
      workflow-backed store so suspended runs survive restarts.
- [ ] **Replay dashboard** — pull, lint, and replay captured event logs in the UI.

The canonical, live version of this list is the session task tracker; this file
mirrors it for anyone reading the repo.
