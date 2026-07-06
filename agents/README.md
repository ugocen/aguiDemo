# Scenario agents

Scenario-specific agents, kept separate from the core demo agents in
`backend/app/agent/`. Each one maps to a canonical
[AG-UI Dojo](https://dojo.ag-ui.com/) feature and showcases a distinct
combination of AG-UI message types, so the sidebar can switch between clearly
different behaviors. In `langgraph` mode with a provider key the model drives the
cards (limited to each agent's `allowed_tools`); otherwise a scripted fallback
runs, so the demo and the smoke work without credentials. `content-studio` is
always scripted (the canvas has no tool).

| Agent id | Class | AG-UI feature | Card types exercised |
| --- | --- | --- | --- |
| `research-desk` | `ResearchDeskAgent` | agentic chat + reasoning | reasoning, lookup, table, citations, suggested questions |
| `trip-architect` | `TripArchitectAgent` | subgraphs + HITL | reasoning, steps, form, table, chart, approval, follow-up, suggested questions |
| `incident-commander` | `IncidentCommanderAgent` | agentic generative UI (live steps) + HITL | reasoning, steps, lookup, table, chart, approval, follow-up |
| `growth-analyst` | `GrowthAnalystAgent` | tool-based generative UI | reasoning, table, chart, follow-up, suggested questions |
| `content-studio` | `ContentStudioAgent` | predictive state updates (canvas) | reasoning, canvas edits, follow-up, approval (HITL) |

## How they are wired

- Each agent implements the same interface as the core agents: an async
  generator `run(input)` yielding the semantic events in `app.agent.events`.
  Only the translator emits AG-UI protocol events, so these agents stay pure.
- `registry.py` maps agent id to class and exposes `scenario_descriptors()`.
- The backend `/agents` endpoint lists these, so they appear in the sidebar.
- The frontend sends the selected agent id in `RunAgentInput.forwardedProps`,
  and `app.agent.factory.build_agent` routes to the matching scenario agent.
- Because they route through the same translator, they are also deployable to
  AgentCore via `deploy/agentcore/` without changes.

## Adding a scenario

1. Add a class with `id`, `name`, `description`, `mode = "scenario"`, and an
   async `run(input)`. For a model-driven agent, also add a `system_prompt` and
   an `allowed_tools` list (catalog constants); omit both to stay scripted-only.
2. Register it in `registry.py`.
3. It shows up in the sidebar and is selectable immediately.
