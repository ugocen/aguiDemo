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
- [x] Run control: a Stop button plus aborting the in-flight/suspended run when
      switching agents or resetting, so a HITL-suspended run never wedges the
      composer (`store.beginRun`/`stopRun`, `runAgent` gets an AbortSignal).
- [x] Default model-driven agent ("General Assistant") is selectable in the
      sidebar; it routes to the fallback LangGraph/mock agent.
- [x] Reproducible EKS bring-up/teardown scripts (`deploy/eks/deploy.sh`,
      `deploy/eks/teardown.sh`) that keep the ACM cert + ECR images.
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
    - [x] `editDocument` tool — the model writes/revises the canvas; the LLM
          agent maps the call to a document delta. Verified live (real Gemini
          emits a `STATE_DELTA` on `/document/content`).
- [x] **Entra sign-in wired** — MSAL (PKCE, ID token) in `frontend/lib/auth.ts`,
      config filled from the `agui-test` app registration, backend validates
      (issuer + audience = client id). Dev mode stays the default; flip
      `AUTH_MODE`/`NEXT_PUBLIC_AUTH_MODE` to `entra` and sign in to use it. The
      interactive login needs a real browser (cannot verify headless).
- [x] **Shared state in CopilotKit mode** — `CopilotSharedStatePanel` reads
      `useCoAgent` and shows the live cart/quiz (same hook as the canvas). Build-
      verified; full runtime needs the CopilotKit client in a browser.
- [ ] **AgentCore deploy** (Phase 2) and **EKS deploy** (Phase 3) — run the
      prepared manual steps (needs AWS). First run `/aws-bootstrap` once with root
      to create the scoped `agui-deployer` IAM user, then deploy with that profile
      (`deploy/aws/`).
- [x] **Durable HITL** — the resume registry is now DB-backed (`pending_approvals`
      table): decisions are written through, order-independent, and survive a
      restart (a fresh registry reads the decision from the DB). Falls back to
      in-memory when no DB is configured. `GET /agui/approvals` lists pending ones.
      (Resuming a run's coroutine after a mid-run crash still needs graph
      checkpointing; the decision channel is what is durable.) Tested in
      `tests/test_durable_hitl.py`.
- [x] **Replay dashboard** — `GET /agui/runs` + `list_run_logs` list captured
      runs; the `ReplayPanel` re-plays a run's recorded events back through the
      store (play/pause/step/restart/speed) so the whole run renders again. The
      playback loop uses a virtual clock so pace is correct and renders stay
      bounded. Browser-verified (replayed a run's cards + HITL cart faithfully).

The canonical, live version of this list is the session task tracker; this file
mirrors it for anyone reading the repo.
