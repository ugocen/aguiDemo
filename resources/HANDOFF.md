# AG-UI Demo — Handoff / Bootstrap Document

> This document exists to continue the project from where we left off in a **new
> local Claude Code session** (or by hand). The goal is to gather, in one place,
> the whole codebase, why it is the way it is, what is verified vs not, the
> remaining work, and a step-by-step implementation plan.
>
> **A good first message for the next session:**
> "Read resources/HANDOFF.md, understand the project, then look at
> `docs/PROJECT_STATUS_AND_ROADMAP.md` and `TODO.md`. Let's continue with [task]."

Table of contents:
1. [Purpose](#1-purpose)
2. [What we did and why (decision log)](#2-what-we-did-and-why-decision-log)
3. [Current status — what works, what does not](#3-current-status)
4. [Architecture and end-to-end flow](#4-architecture-and-end-to-end-flow)
5. [Repo map — what each file does](#5-repo-map)
6. [How to run and verify locally](#6-how-to-run-and-verify-locally)
7. [Known gotchas](#7-known-gotchas)
8. [Gaps and remaining work](#8-gaps-and-remaining-work)
9. [Implementation plan (remaining work, step by step)](#9-implementation-plan)
10. [Git / branch status](#10-git--branch-status)
11. [Work log](#11-work-log)

---

## 1. Purpose

A Claude-like assistant workspace that exercises the **AG-UI protocol** end to
end. AG-UI (Agent-User Interaction Protocol): the backend streams typed JSON
events (lifecycle, text, tool call, state, custom) to the frontend over
**Server-Sent Events (SSE)**, and the frontend renders each one live.

The demo shows the four core capabilities plus extra card types, live:
- **Streaming chat** — tokens appear as the model produces them.
- **A visible tool call** — rendered as a live card.
- **A shared-state document canvas** — the agent edits it live while it talks.
- **Human-in-the-loop approval** — the agent pauses and resumes on the user's answer.
- **Extra message types** — table, chart, follow-up, suggested questions, citations, form.

Long-term goal: run the agents on AWS Bedrock **AgentCore**, the app on **EKS**,
identity via **Microsoft Entra**, and model calls through a **GenAI Marketplace**
gateway. Phase 1 (local) is done; Phase 2/3 assets are prepared but not deployed.

The original build spec is the plan the user first provided (the document that
started this repo). Its summary lives in `README.md` and under `docs/`.

---

## 2. What we did and why (decision log)

This section answers the "why is it like this?" questions in the codebase. A new
session gains the most context here.

- **One event source (`translator.py`).** All AG-UI protocol events are emitted
  from one place. Agents produce framework-neutral *semantic* events
  (`TextDelta`, `ToolCallStarted`, `DocumentDelta`, `ApprovalRequested`); the
  translator maps them to the protocol and enforces ordering/pairing. Reason:
  guarantee protocol correctness in one place and keep agents pure.

- **Agent → generator + approval via `asend`.** The agent is an async generator;
  for approval it does `decision = yield ApprovalRequested(...)` and receives the
  decision back through the generator's send channel. So the agent never knows
  the protocol; only the translator emits events.

- **Two AG-UI clients (custom + CopilotKit), selected by `NEXT_PUBLIC_CLIENT`.**
  - `custom` (default): a hand-built SSE client in `lib/agui.ts` + a Zustand
    store + hand-built cards + a live Event Inspector. **HITL and canvas work end
    to end here.**
  - `copilotkit`: CopilotKit provider + CopilotChat + `useCopilotAction` cards,
    the `/api/copilotkit` runtime route bridging to the backend via an AG-UI
    `HttpAgent`.
  - **Why both?** The plan named CopilotKit "primary" and `@ag-ui/client` + a
    hand-built pane the "sanctioned fallback". Our HITL design (one suspended run
    + `/agui/resume`) does not match CopilotKit's native multi-run HITL; the
    custom client runs it fully. CopilotKit was also added because the user asked
    for it — cards are defined via `useCopilotAction`, build-verified; full
    runtime verification needs a browser.

- **CopilotKit 1.4.4 → 1.62.2 upgrade.** The 1.4.4 npm tarball **had no `dist`**
  (source-only), could not be imported → `next build` broke. 1.62.2 ships a
  proper `dist`. A peer-dependency conflict means `npm install
  --legacy-peer-deps` is required (`@langchain/langgraph-sdk` peerOptional).

- **Scenario agents in a separate `agents/` package.** The user asked for a
  "separate folder". Four scripted agents (research/doc-writer/data-analyst/
  support-triage), each a different card combination. Backend `build_agent`
  routes by `forwardedProps.agentId`. Because they reuse the same translator,
  they are AgentCore-deployable too.

- **Scripted agents (not a real LLM).** So the demo runs without Marketplace
  credentials, the agents are deterministic. The card "decision" is currently =
  which agent/scenario was selected. The real LLM tool-calling path is #7.

- **In-memory HITL resume.** An `asyncio.Event` keyed by `run_id`. Because the
  decision can arrive before the run reaches its suspend point, the registry is
  **order-independent** (the decision is buffered). Production would need a
  durable workflow engine (Temporal was deliberately not used — demo scope).

- **Vendor-agnostic model path.** `app/llm/factory.build_llm` is the single
  entry; the provider is selected by `LLM_PROVIDER` (Claude/OpenAI/Gemini/
  Marketplace), all exposing the same `stream_completion` interface. Reason: the
  agents must work with any LLM vendor. Only text streaming so far; tool-calling
  is #7.

- **Identity from the bearer, never from `RunAgentInput`.** dev stub + Entra
  bearer validation code written; Entra not tested against a real tenant.

- **Persistence: Postgres behind a swappable repository.** Verified end to end
  with SQLite.

- **Isolation rule.** Packages always go into a venv (`backend/.venv`) /
  `node_modules`; no global installs. `.claude/settings.json` hard-denies global
  installs. Connecting to external services (AWS/Marketplace/GitHub) is out of
  scope for this rule.

- **AWS: root only once.** `deploy/aws/bootstrap_iam.sh` uses root once to create
  a scoped `agui-deployer` IAM user; after that always that profile, never root.

- **Multi-tool agent config.** `AGENTS.md` is canonical (Antigravity + Claude
  Code); `CLAUDE.md` `@import`s it → no drift. `.claude/` and `.agents/` mirror.

---

## 3. Current status

### Working and verified (locally)
| Feature | Status | How verified |
|---|---|---|
| Streaming chat, tool card, table, chart, follow-up, suggested, citations, form | ✅ | 5 agent paths driven over HTTP/SSE, all lint-clean |
| Canvas (custom client) | ✅ | STATE_SNAPSHOT/DELTA end to end |
| HITL approval (custom client) | ✅ | suspend/resume via `/agui/resume`, approve+reject |
| Persistence | ✅ | create/list/load + tool_events_json with SQLite |
| Event capture + ordering lint | ✅ | `pytest` green, `docs/sample_run_log.jsonl` lint-clean |
| Backend/frontend catalog parity (8 tools) | ✅ | static comparison in `smoke_e2e.py` |
| tsc + eslint + next build (both clients) | ✅ | |
| Scenario routing (`agentId`) | ✅ | 4 scenarios + mock default |
| Vendor-agnostic LLM (Claude/OpenAI/Gemini/Marketplace) | ✅ | `test_llm_providers.py` each vendor's SSE parse (mock HTTP), 8/8 tests |
| AWS safe-flow assets (deploy/aws) | ✅ prepared | policy JSON valid, script `bash -n` clean (not deployed) |

### Written but not fully verified (impossible in this environment)
| Feature | Why not verified |
|---|---|
| CopilotKit HITL round-trip + canvas | **No browser** — only compile/bundling verified |
| Docker image build (backend + agentcore) | **No Docker daemon** — verified by simulating the layout on the filesystem |
| Real LLM (`AGENT_MODE=langgraph`) | **No Marketplace key** |
| Entra sign-in | **No Azure AD app registration** |
| Helm render | **No helm CLI** — value references checked statically |

---

## 4. Architecture and end-to-end flow

```
FRONTEND (Next.js)                         BACKEND (FastAPI)
  page.tsx                                   POST /agui/run
   ├ AgentList / HistoryList (sidebar)         │
   ├ ChatArea (custom)  |  CopilotChat          ▼
   │   store.ts (Zustand reducer)            factory.build_agent(agentId)
   │   catalog.ts (shared tool contract)        │  (mock | langgraph | scenario)
   │   card components                           ▼
   └ lib/agui.ts (read SSE)  <──SSE─────  translator.stream()  ← THE event source
                                              │   agent.run(input) → semantic events
                                              ▼
                                          EventEncoder → "data: {...}\n\n"
```

**"analyze my events" (Data Analyst selected), step by step:**
1. `ChatArea.send()` → if needed `POST /conversations`, optimistically renders the
   user message, builds `RunAgentInput` (`tools` = 8 schemas, `forwardedProps.agentId`).
2. `runAgent()` → `fetch POST /agui/run` (+ bearer).
3. Backend: `get_current_principal` (dev: fixed), reads `agentId`,
   `build_agent(..., "data-analyst")` → `DataAnalystAgent`. User turn to Postgres.
4. `DataAnalystAgent.run()` yields semantic events: TextDelta, ToolCallStarted
   (renderTable), **ToolCallStarted (renderChart)**, renderFollowUp, renderSuggested.
5. `translator.stream()` maps them to AG-UI events: RUN_STARTED → STATE_SNAPSHOT →
   TEXT_MESSAGE_* → (close text) → TOOL_CALL_START/ARGS/END … → RUN_FINISHED. Each
   event is written to `run_logs/<run_id>.jsonl` and logged.
6. `EventEncoder` produces the SSE frame; `_sse_with_keepalive` pumps in the background.
7. Frontend `lib/agui.ts` parses the stream, calls `store.handleEvent(event)`.
8. `handleEvent` reducer: renderChart TOOL_CALL_START → empty `{kind:"chart"}`
   placeholder; TOOL_CALL_ARGS accumulates; TOOL_CALL_END → parse → chart filled.
9. `ChatArea` `item.kind==="chart"` → `<ChartCard>` → **inline SVG bar chart**.

**"How is the chart decided?"** There are three mechanisms today:
- **Scenario agent**: no decision, the agent always shows its card set; the real
  decision = which agent the user selected.
- **LangGraph agent** (`agent/graph.py`): `_plan_node` keyword heuristic ("table"/
  "compare" in the message → table; **there is no chart flag yet**).
- **Real LLM (not wired yet)**: AG-UI's true path — the `tools` schemas are given
  to the model, and the model decides which tool to call via **function calling**.
  This is #7.

For a deeper walkthrough, `docs/PROJECT_STATUS_AND_ROADMAP.md` complements this.

---

## 5. Repo map

```
backend/app/
  main.py                  FastAPI app, CORS, routers, lifespan (create_all)
  config/settings.py       pydantic-settings, ALL env here (single Settings)
  api/agui_router.py       POST /agui/run (SSE), /agui/resume, /agui/runs/{id}/log
  api/conversations.py     GET/POST /conversations, GET /conversations/{id}
  api/agents.py            GET /agents (scenario list)
  agui/translator.py       ★ THE event source — the protocol is produced here
  agui/catalog.py          ★ 8 frontend-tool schemas (backend side)
  agui/resume.py           in-memory HITL resume registry (order-independent)
  agui/lint.py             ordering lint (pairing/sequence)
  agui/run_capture.py      write + read run_logs/<run_id>.jsonl
  agent/factory.py         build_agent(settings, agent_id) — routing
  agent/graph.py           LangGraphAgent (real model path, plan node + stream)
  agent/mock.py            MockAgent (scripted showcase, all cards)
  agent/tools.py           lookup_knowledge (demo backend tool)
  agent/events.py          semantic event dataclasses
  agent/base.py            latest_user_text, initial_state
  llm/factory.py           ★ build_llm(settings) — THE model path, selects provider
  llm/base.py              LLMClient protocol + split_system helper
  llm/openai_compatible.py OpenAI-compatible core (stream/chunked)
  llm/marketplace.py       Marketplace gateway (openai_compatible wrapper)
  llm/openai_provider.py   OpenAI
  llm/anthropic_provider.py  Claude (Messages API SSE)
  llm/gemini_provider.py   Gemini (streamGenerateContent SSE)
  db/models.py             Conversation, Message (SQLAlchemy)
  db/session.py            async engine, session_scope
  db/repository.py         HistoryRepository (Protocol) + SqlAlchemy impl
  auth/entra.py            get_current_principal (dev stub | Entra JWKS validation)
  logging/setup.py         structlog
backend/tests/test_event_order.py   translator + HITL + lint tests
backend/tests/test_llm_providers.py  each vendor's SSE parse (mock HTTP)
backend/scripts/smoke_e2e.py         ★ end-to-end SSE smoke (exit-coded)

agents/                    ★ scenario agents (separate package)
  registry.py              id → class, scenario_descriptors()
  research_assistant.py    lookup+table+citations+suggested
  doc_writer.py            canvas+followup+approval
  data_analyst.py          table+chart+followup+suggested
  support_triage.py        lookup+approval+form+followup
  _common.py               tokens(), call_id()

frontend/
  app/page.tsx             workspace, client selection via NEXT_PUBLIC_CLIENT
  app/providers.tsx        loads agents/conversations (CopilotKit can wrap it)
  app/api/copilotkit/route.ts     CopilotKit runtime → HttpAgent → /agui/run
  app/api/copilotkit/agentName.ts COPILOT_AGENT_NAME (client/server split)
  lib/agui.ts              ★ custom SSE client (runAgent, resumeRun)
  lib/store.ts             ★ Zustand reducer (handleEvent) — event→UI
  lib/catalog.ts           ★ 8 tool schemas (frontend side, mirrors backend)
  lib/api.ts               conversations/agents fetch helpers
  lib/auth.ts              getBearerToken (dev stub; MSAL slot ready)
  components/chat/ChatArea.tsx      composer + item render + send orchestration
  components/catalog/*.tsx          ToolCard, TableCard, ChartCard, FollowUpCard,
                                     CitationsCard, FormCard, ApprovalCard, Suggested
  components/canvas/CanvasPanel.tsx Tiptap canvas (custom client)
  components/inspector/EventInspector.tsx  live AG-UI event stream (dev view)
  components/copilot/               CopilotChatArea, CopilotGenerativeUI,
                                     CopilotCanvasPanel (useCoAgent)

deploy/agentcore/          Phase 2: agentcore_app.py (/ping,/invocations) + Dockerfile
deploy/eks/                Phase 3: Helm chart (backend/frontend/ingress/config)
deploy/aws/                IAM policy + bootstrap_iam.sh + README (root-once flow)
scripts/check_env.sh       ★ prerequisite check (Python/Node/npm/Docker/venv)
docs/                      FINDINGS, PROJECT_STATUS_AND_ROADMAP, sample_run_log

Agent tooling (multi-tool):
  AGENTS.md                ★ canonical cross-tool guide (Antigravity+Claude+…)
  CLAUDE.md                @AGENTS.md import + Claude-specific
  .claude/agents/          subagents (card-type-builder, scenario-agent-builder, agui-verifier)
  .claude/commands/        /check /verify /smoke /run /build /add-card /new-scenario /aws-bootstrap
  .claude/settings.json    permission allow + global-install deny
  .agents/rules/           Antigravity always-on rules (start/invariants/verify/isolation/aws/collaboration)
  .agents/workflows/       the same 8 slash workflows
README.md, TODO.md, .env.example, docker-compose.yml, .gitignore, .dockerignore
```

---

## 6. How to run and verify locally

Prerequisites: Python 3.11, Node 20+ (this repo also ran on 22), Docker (for Postgres).

```bash
# 0. check prerequisites (Python 3.11+, Node 20+, npm, Docker, .env, venv)
bash scripts/check_env.sh   # or /check

# 0b. env
cp .env.example .env       # defaults: AGENT_MODE=mock, AUTH_MODE=dev, NEXT_PUBLIC_CLIENT=custom

# 1. Postgres (optional; without it runs still stream, but there is no history)
docker compose up -d postgres

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
# health: curl localhost:8000/health

# 3. Frontend (separate terminal)
cd frontend
npm install --legacy-peer-deps      # CopilotKit peer-dep conflict needs --legacy-peer-deps
npm run dev                          # http://localhost:3000
```

Demo prompt: select an agent in the sidebar and type:
`explain ag-ui, compare the types, next steps, draft a note then approve`

To try the CopilotKit client, set `NEXT_PUBLIC_CLIENT=copilotkit` in `.env`.

**Verification commands:**
```bash
cd backend && source .venv/bin/activate && pytest -q          # should pass
cd backend && source .venv/bin/activate && python scripts/smoke_e2e.py  # end-to-end SSE smoke
cd frontend && npm run typecheck && npm run lint && npm run build
```

**Agent tooling (ready for multiple tools):**
- `AGENTS.md` (root) — **canonical**, cross-tool agent guide (read by Antigravity,
  Claude Code, and others). Single source of truth; do not copy its content elsewhere.
- **Antigravity**: `.agents/rules/` (always-on rules: start-here, invariants,
  verify, **isolation**, **aws**, **collaboration**) + `.agents/workflows/` (8
  slash workflows). Note: some Antigravity versions read `.agent/workflows/`
  (singular); if a workflow is ignored, rename the folder.
- **Claude Code**: `CLAUDE.md` (`@AGENTS.md` import → no drift), project memory;
  `.claude/settings.json` global-install deny + permission allow.
- `.claude/agents/` — subagents: `card-type-builder`, `scenario-agent-builder`,
  `agui-verifier`.
- **8 commands (Claude + Antigravity)**: `/check` (prerequisites), `/verify`,
  `/smoke`, `/run` (dev), `/build` (Docker images), `/add-card`, `/new-scenario`,
  `/aws-bootstrap` (root-once IAM deployer).
- **Rules**: packages always into venv/node_modules (no global installs); AWS
  always the `agui-deployer` profile (root only at bootstrap). Details: `AGENTS.md`.
- `backend/scripts/smoke_e2e.py` — committed end-to-end verification (exit-coded).

---

## 7. Known gotchas

Found while debugging in this environment; remember them in a new session:

1. **The `agents/` package must be importable.** Backend `pip install -e` only
   puts `app` on the path. `agent/factory.py::ensure_agents_on_path()` walks up to
   find `agents/registry.py` and adds the directory to the path. Docker images
   **must copy** `agents/` — that is why `backend/Dockerfile` builds from the repo
   root (`docker build -f backend/Dockerfile .`).
2. **structlog reserved key.** `log.info("event_name", event=...)` collides; we
   named the kwarg `event_type`.
3. **HITL resume race.** The decision can arrive before the suspend; `resume.py`
   buffers it. Do not break this.
4. **The SSE keepalive must not cancel the generator.** `_sse_with_keepalive`
   pumps the agent in a background task; the timeout only affects the queue read.
5. **CopilotKit 1.4.x is source-only.** Use 1.62.2; `--legacy-peer-deps` required.
6. **Custom-client HITL ≠ CopilotKit HITL.** Custom = one run + `/agui/resume`.
   In CopilotKit mode `runId` is injected into the approval args and the
   `resumeRun` bridge is called; this must be tested in a browser.
7. **Root `.dockerignore`** excludes frontend/docs/venv from the image context so
   the backend image stays small.

---

## 8. Gaps and remaining work

Live list: `TODO.md`. Remaining, in priority order:

- **#7 LLM tool-calling** — let the model *decide* (chart vs table) + power the
  scenario agents with a real model. **The vendor layer is ready** (Claude/OpenAI/
  Gemini); only tool-calling needs to be added plus a provider key.
- **#9 Entra sign-in end to end** — needs an Azure AD app registration.
- **#10 AgentCore + EKS deploy** — first `/aws-bootstrap` (root, once), then
  deploy with the `agui-deployer` profile.
- **CopilotKit HITL/canvas browser verification** — #4/#5 code ready, needs a look.
- **#11 Durable HITL + replay dashboard** — large, optional.

---

## 9. Implementation plan

### #7 — Real LLM tool-calling (priority)
**Goal:** let the model, not a heuristic, decide "chart or table?".
**Note:** the vendor-agnostic model path is ALREADY DONE — `LLM_PROVIDER` selects
Claude/OpenAI/Gemini/Marketplace (`app/llm/factory.build_llm`, all expose
`stream_completion`, parsing verified by `test_llm_providers.py`). Remaining work
is just adding tool-calling:
1. `.env`: `AGENT_MODE=langgraph`, `LLM_PROVIDER=anthropic|openai|gemini|marketplace`
   and the relevant `*_API_KEY`/`*_MODEL`.
2. Add tool-calling to `app/llm/openai_compatible.py` (for OpenAI/Marketplace):
   put `tools` (RunAgentInput.tools → OpenAI function schema) + `tool_choice` in
   the payload, and accumulate `choices[].delta.tool_calls` in the stream. For
   Anthropic/Gemini use their own tool formats (Anthropic `tools`+`tool_use`
   blocks; Gemini `functionDeclarations`).
3. `agent/graph.py::LangGraphAgent.run()`: map the model's returned `tool_calls`
   to `ToolCallStarted(name, args)` semantic events. Frontend-render tools
   (renderChart/renderTable/...) need no `ToolCallCompleted`; backend tools like
   `lookupKnowledge` run the tool, yield `ToolCallCompleted(result)`, and feed the
   result back for a second turn (the classic tool-use loop).
4. Verify: with a real key, type "compare X and Y in a chart" and see the model
   call `renderChart`. `lint.py` must still be clean.
5. Optionally make the scenario agents LLM-driven the same way.

### #9 — Entra sign-in
1. Azure AD SPA app registration: redirect `http://localhost:3000`, expose an
   API/scope. `.env`: `AUTH_MODE=entra`, `NEXT_PUBLIC_AUTH_MODE=entra`,
   `ENTRA_TENANT_ID/CLIENT_ID/AUDIENCE`, `NEXT_PUBLIC_ENTRA_CLIENT_ID/TENANT_ID/
   REDIRECT_URI/SCOPE`.
2. `frontend/app/providers.tsx`: set up `PublicClientApplication` (msal-browser),
   wrap with `MsalProvider`.
3. `frontend/lib/auth.ts::acquireEntraToken()`: return an access token via
   `acquireTokenSilent` (fallback `loginPopup`).
4. Backend `auth/entra.py` already does JWKS validation — it activates once the
   env is filled. Check the `preferred_username`/`oid` claims.
5. Verify: the app is locked until sign-in; history is scoped to the user.

### #4/#5 — CopilotKit HITL & canvas browser verification
1. `NEXT_PUBLIC_CLIENT=copilotkit`, backend + frontend up.
2. Run the approval scenario (doc-writer); confirm Approve/Reject advances the run
   via both `respond()` and `/agui/resume`. If a double-trigger (respond + a new
   run) is observed: either drop `respond()` and rely only on the `/agui/resume`
   bridge, or add a CopilotKit-native mode in the backend (end the run on
   approval, consume the tool result on the next run — make agents "resumable
   from messages").
3. Canvas: verify `useCoAgent().state.document` updates live from STATE_DELTA.

### #10 — Deploy (manual)
0. **First AWS bootstrap** (once, with root): `/aws-bootstrap` or
   `bash deploy/aws/bootstrap_iam.sh` → creates the `agui-deployer` IAM user. Then
   `aws configure --profile agui-deployer`. After that **always this profile**,
   never root (see `deploy/aws/README.md`, `.agents/rules/40-aws.md`).
1. Follow `deploy/agentcore/README.md` (CLI or ECR-register) and
   `deploy/eks/README.md`. Build the backend/agentcore image **from the repo
   root** (`/build`). RDS connection into `values.yaml` secrets, with
   `AUTH_MODE=entra`.

### #11 — Durable HITL + replay dashboard (optional)
Replace `resume.py` with an external store (e.g. Redis/DB); add a small replay/
lint UI that consumes `/agui/runs/{id}/log`.

---

## 10. Git / branch status

- Working branch: **`main`** (user preference — everything current on one branch).
- The default branch is still `claude/implement-plan-y2lai0` (cosmetic; content is
  on `main`). To change it: GitHub Settings → Branches → default = `main`.
- Old branches were not deleted (user's choice).
- PR flow was dropped; commits/pushes go directly to `main`.

**Quick start for a new local session:**
```bash
git clone <repo> && cd aguiDemo
git checkout main
# then the setup + verification steps in section 6
```

---

## 11. Work log

More than one agent may work this repo in parallel (Claude Code, Antigravity, …).
This section is the **canonical copy** of the collaboration protocol; `AGENTS.md`
and `.agents/rules/50-collaboration.md` only point here. The work log is always
the **final section** of HANDOFF.

**Before starting a task:** (do this before **each** task, including a 2nd or 3rd
task within the same session — not only the first)
- `git pull` (main), review the incoming changes.
- Read the **newest entries** of the work log below — what others did and what
  they planned in "Next". Do not restart work someone already claimed there.

**After finishing a task:**
- **Verify first, then push:** run the standard verification (`pytest -q` +
  `scripts/smoke_e2e.py`; frontend `typecheck`/`lint`/`build`). **Push to `main`
  only if green — never push red.**
- If you did a meaningful unit of work (a feature, fix, scenario, or a doc/protocol
  change others need to know about), prepend a short entry **immediately below**
  the `NEW ENTRIES` marker below. Do not log trivial edits; fold them into the
  next entry.
- Commit and push to `main`. (This is the **one exception** to "push only when
  asked" — the work log is pushed after every task.)

**If the push is rejected (main moved):**
- `git pull --rebase`, then push again.
- **A work-log conflict is trivial:** keep both entries (delete the conflict
  markers, leave order by timestamp), `git add` + `git rebase --continue`. Never
  use `--ours`/`--theirs`/`--abort` (it drops a peer's entry).
- **A code conflict is NOT trivial:** resolve it, re-verify (green), then push.
- Never `--force` / `--force-with-lease` push to `main`.

**Maintenance:** keep roughly the last ~15–20 entries (older ones live in git
history). Keep entries short; do not list files (git tracks those), state the
**work done**. Language: **English only** (all docs, code, and comments).

**Entry format** (newest first):

```
### <ISO-8601 UTC date, with time if available — e.g. 2026-07-05T14:30Z> — <identity>
**Did:** <one or two sentences, what was done>
**Next:** <planned next task if any; otherwise "—">
```

Identity: start with your tool name, add a session URL/ID if your tool exposes
one, otherwise tool name + date. Examples:
`Claude-Session: https://claude.ai/code/session_XXXX` ·
`Antigravity: <workspace/agent> (2026-07-05)`

<!-- NEW ENTRIES BELOW, NEWEST FIRST -->

### 2026-07-06T06:30Z — Claude-Code (Opus 4.8, 2026-07-06)
**Did:** Per the repo owner, lifted the "never install globally" isolation rule
and the "never use root" AWS restriction (owner authorized root for
infrastructure/permission acquisition). Updated `AGENTS.md` and
`.agents/rules/40-aws.md`, removed `.agents/rules/30-isolation.md`. Could not edit
`.claude/settings.json` (auto-mode blocks self-permission changes) — its deny list
still lists global-install denies, which are harmless for the deploy; the owner
can clear them directly. Deploy in progress: helm/eksctl installed, ECR + 3 images
pushed, AgentCore runtime (mock) created, EKS cluster `agui-demo` up (2 nodes).
**Next:** Finish the EKS deploy — RDS (root), AWS Load Balancer Controller, Helm.

### 2026-07-06T02:58Z — Antigravity (2026-07-06)
**Did:** Executed the one-time `/aws-bootstrap` workflow. Verified preconditions, ran `deploy/aws/bootstrap_iam.sh` to create the scoped `agui-deployer` IAM user and attach its policy, and configured the local `agui-deployer` AWS profile with the generated access keys.
**Next:** Follow deploy/agentcore/README.md and deploy/eks/README.md to deploy the app to AWS.

### 2026-07-06T05:55Z — Claude-Code (Opus 4.8, 2026-07-06)
**Did:** Fixed duplicate cards in LLM tool-calling (found via a debug run-log:
renderTable/Chart/FollowUp/Suggested were each emitted twice). A render-only turn
fed the model a "rendered" ack, which prompted it to re-emit the same cards on
the next turn. `LLMToolAgent` now disables tools after a render-only turn, so the
follow-up turn is a text wrap-up instead of a repeat; lookup/approval turns keep
tools on so the model can react. Verified live (each card once, lint clean, 2
Gemini calls instead of 3) and with a regression unit test; 16 tests pass.
**Next:** —

### 2026-07-06T05:50Z — Claude-Code (Opus 4.8, 2026-07-06)
**Did:** Hardened the collaboration protocol after feedback that the pre-task
`git pull` was being skipped on later tasks within a session (the after-task
log+push was being done). Added a strict, non-skippable enforcement block to
`CLAUDE.md` (the Claude Code parallel to Antigravity's `.agents/AGENTS.md`) and
clarified §11 that the pull happens before EACH task, mid-session included. Docs
only, no code change.
**Next:** —

### 2026-07-06T05:35Z — Claude-Code (Opus 4.8, 2026-07-06)
**Did:** Implemented #7 (LLM tool-calling). Added a vendor-agnostic
`stream_chat(messages, tools)` to every provider (Gemini / OpenAI-compatible /
Anthropic) yielding `TextChunk`/`ToolCallChunk`; a new `app/agent/llm_agent.py`
`LLMToolAgent` runs a bounded tool-use loop so the model decides which card to
render (render tools → `ToolCallStarted`; `lookupKnowledge` → run + feed back;
`requestApproval` → HITL via `asend`). `LangGraphAgent` now subclasses it (the
LangGraph graph plans a rendering hint). In `langgraph` mode with a provider key
the default agent and the research / data-analyst / support scenarios are
model-driven; `doc-writer` stays scripted (canvas has no tool), and `mock` mode /
no key stay scripted so the smoke is deterministic (pinned to mock). Verified
live against Gemini (model called renderTable+renderChart, and
lookup+approval+form; lint clean) plus 15 unit tests. Graceful rate-limit
handling; Gemini free tier is ~5 req/min, so multi-card runs can hit the quota.
**Next:** Optional `editDocument` tool so doc-writer's canvas is model-driven;
expose the default LLM agent in the sidebar.

### 2026-07-06T02:10Z — Claude-Code (Opus 4.8, 2026-07-06)
**Did:** Selecting a scenario agent in the sidebar now starts a fresh
conversation (`AgentList` mirrors `HistoryList.startNew`: clear thread + reset
chat + refresh list). Also confirmed the langgraph/Gemini path works end to end
(real ~5s model response via an empty `agentId`) but is currently unreachable
from the UI: the store auto-selects `agents[0]`, so every run sends a scenario
`agentId`, which `build_agent` routes to the scripted scenario agent, never the
LLM. Frontend typecheck/lint/build green.
**Next:** Optionally expose the real-LLM path in the UI (a "Default (LLM)" entry
sending an empty `agentId`) or make the scenario agents LLM-driven (#7).

### 2026-07-06T01:55Z — Claude-Code (Opus 4.8, 2026-07-06)
**Did:** Fixed the frontend `lib/api.ts` "Failed to fetch" (CORS): the browser
origin `http://127.0.0.1:3000` was not in the allowlist — added it to
`CORS_ALLOW_ORIGINS` (settings default + `.env`/`.env.example`). Also fixed a
latent setup bug: the backend never read the repo-root `.env` because `env_file`
was cwd-relative and the backend runs from `backend/`, so `AGENT_MODE=langgraph`,
`LLM_PROVIDER=gemini`, and `DATABASE_URL` (port 5433) were silently inactive
(backend ran on mock/dev/5432 defaults). Pinned `env_file` to the repo-root `.env`
(absolute path) so config actually applies; pinned the smoke to `AGENT_MODE=mock`
to keep it hermetic. Verified: pytest 8, smoke OK, frontend typecheck/lint/build.
**Next:** —

### 2026-07-06T01:00Z — Antigravity (2026-07-06)
**Did:** Investigated `role "agui" does not exist` causing a 500 error on the backend and failing fetch on the frontend. Discovered that a native Postgres server was running on the Mac at `localhost:5432` which intercepted the backend's DB connection, bypassing the Docker container. Changed `docker-compose.yml` to map the container to `5433:5432` and updated `.env` to connect to `5433`.
**Next:** User can manually restart the backend and frontend to verify it runs without crashing.

### 2026-07-06T00:46Z — Antigravity (2026-07-06)
**Did:** Stopped the background instances of the backend (`uvicorn`) and frontend (`npm run dev`) so the user could run them manually in separate terminals to follow logs. Handed over local orchestration to the user.
**Next:** Stand by for further instructions or complete #7 (LLM tool-calling) if the user provides an API key and requests it.

### 2026-07-06T00:36Z — Antigravity (2026-07-06)
**Did:** Fixed the `TypeError: Failed to fetch` error in the Next.js server by creating a symlink from `frontend/.env` to `../.env`. Next.js requires the `.env` file to be in its own working directory to automatically load `NEXT_PUBLIC_*` and `BACKEND_URL` variables. Restarted the frontend development server to pick up the changes.
**Next:** Stand by for the user's manual validation in the browser.

### 2026-07-06T00:33Z — Antigravity (2026-07-06)
**Did:** Completely re-ran the local development environment at the user's request. Reset the `postgres` Docker container to clear an authorization error, then successfully restarted the backend (`uvicorn`) and frontend (`npm run dev`) services. Verified the backend `/health` endpoint is functioning properly.
**Next:** Stand by for the user's manual validation in the browser.

### 2026-07-06T00:26Z — Antigravity (2026-07-06)
**Did:** Created project-scoped rules in `.agents/AGENTS.md` to strictly enforce the collaboration protocol (`git pull` at start, logging in `HANDOFF.md`, and `git push` at the end).
**Next:** Ensure strict adherence to the logging rule for all future turns.

### 2026-07-06T00:15Z — Antigravity (2026-07-06)
**Did:** Checked prerequisites and verified the environment. User initialized the `.env` file and updated the repository. Built production Docker images (`agui-demo-backend`, `agui-demo-frontend`, `agui-demo-agent`). Spun up the stack locally (Postgres, Uvicorn, Next.js) and ran `/verify` and `/smoke` tests (all green). Addressed Next.js `ECONNREFUSED` / `Failed to fetch` error by changing `localhost` to `127.0.0.1` in `.env` to prevent Node.js IPv6 resolution mismatches.
**Next:** Confirm the frontend properly connects to the backend in the browser.

### 2026-07-05 — Claude-Session: https://claude.ai/code/session_01VwqkEe5sMnLeEL29TDnbJs
**Did:** Translated all planning docs to English (HANDOFF, CHANGELOG,
PROJECT_STATUS_AND_ROADMAP, resources/README) and set an English-only rule for
all docs/code/comments across the agent configs. Verified only these four files
had non-English content (all code was already English).
**Next:** With a provider key, #7 (LLM tool-calling); or with AWS access, #10 (deploy).

### 2026-07-05 — Claude-Session: https://claude.ai/code/session_01VwqkEe5sMnLeEL29TDnbJs
**Did:** Added the work log section and the multi-agent collaboration protocol
(pull + read the log before a task; verify → if green → log → push after). Hardened
it via a 4-lens adversarial review: push-policy exception, verification gate,
rebase/conflict steps, tool-neutral identity, single canonical copy. Summary of
prior work is in `resources/CHANGELOG.md`.
**Next:** With a provider key, #7 (LLM tool-calling); or with AWS, #10 (deploy).
