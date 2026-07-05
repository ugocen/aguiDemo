---
description: Create a new scenario agent in the agents/ package
argument-hint: <agent persona and card mix, e.g. "sales assistant using table + form + approval">
---

Create a new scenario agent: $ARGUMENTS

Launch the `scenario-agent-builder` subagent to add it under `agents/`, register
it in `agents/registry.py`, and give it a distinct mix of card types. Have it
verify with `backend/scripts/smoke_e2e.py` (the agent should appear in `/agents`
and its stream must lint clean), then summarize. Do not commit unless I ask.
