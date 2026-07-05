---
description: Add a new AG-UI card/message type end to end
argument-hint: <card name and what it shows, e.g. "timeline of events with dates">
---

Add a new AG-UI card/message type: $ARGUMENTS

Launch the `card-type-builder` subagent to do this end to end (backend catalog,
an agent that emits it, frontend catalog, store reducer, custom component, and
the CopilotKit `useCopilotAction` render), following the established pattern.
Have it verify with `backend/scripts/smoke_e2e.py` and the frontend
typecheck/build, then summarize the files changed. Do not commit unless I ask.
