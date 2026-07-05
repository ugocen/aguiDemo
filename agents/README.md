# Scenario agents

Scenario-specific agents, kept separate from the core demo agents in
`backend/app/agent/`. Each one is a scripted agent (no gateway credentials
needed) that showcases a distinct combination of AG-UI message types, so the
sidebar can switch between clearly different behaviors.

| Agent id | Class | Card types exercised |
| --- | --- | --- |
| `research-assistant` | `ResearchAssistantAgent` | text, lookup tool, table, suggested questions |
| `doc-writer` | `DocWriterAgent` | text, canvas edits, follow-up, approval (HITL) |
| `data-analyst` | `DataAnalystAgent` | text, table, follow-up, suggested questions |
| `support-triage` | `SupportTriageAgent` | text, lookup tool, approval (HITL), follow-up |

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

1. Add a class with `id`, `name`, `description`, and `run(input)`.
2. Register it in `registry.py`.
3. It shows up in the sidebar and is selectable immediately.
