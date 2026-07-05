---
description: Create a new scenario agent in the agents/ package
---

## Steps

Add a new scenario agent that showcases a distinct mix of card types. Read an
existing agent (`agents/data_analyst.py` or `agents/support_triage.py`) first and
copy its shape.

### 1. Create the agent
- `agents/<name>.py`: a class with `id`, `name`, `description`, `mode = "scenario"`,
  and `async def run(self, input) -> AsyncIterator[AgentEvent]`.
- Use helpers from `agents._common` (`tokens`, `call_id`) and tool-name constants
  from `app.agui.catalog`. Yield `TextDelta`, `ToolCallStarted` (render-only cards),
  `ToolCallStarted` + `ToolCallCompleted` (backend tools like `lookupKnowledge`),
  `DocumentDelta` (canvas), and `decision = yield ApprovalRequested(...)` for HITL.

### 2. Register
- Add the class to `_AGENT_CLASSES` in `agents/registry.py`.

### 3. Verify
- `cd backend && python scripts/smoke_e2e.py`: the new agent should appear in the
  `/agents` list and its stream must lint clean. Give it a distinct card mix so it
  is visibly different from the other scenarios.
