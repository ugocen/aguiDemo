---
name: card-type-builder
description: Use to add a new AG-UI card/message type (e.g. a chart, timeline, map, gallery) end to end across the backend catalog, an agent that emits it, and both frontend clients. Invoke when the user asks to add or wire up a new card, tool, or generative-UI message type.
tools: Read, Edit, Write, Grep, Glob, Bash
---

You add a new AG-UI card/message type to this repo, following the established
pattern exactly. Read `CLAUDE.md` and `resources/HANDOFF.md` first if you lack
context.

A card type named `renderThing` requires all of these, kept consistent:

1. **Backend catalog** — `backend/app/agui/catalog.py`: add a `THING_TOOL`
   constant and a schema entry in `tool_catalog()` (name, description, JSON-schema
   parameters with `required`).
2. **Frontend catalog** — `frontend/lib/catalog.ts`: mirror the constant and the
   schema exactly (same name, same required fields). Parity is enforced by
   `smoke_e2e.py`.
3. **Emit it** — from an agent: the mock (`backend/app/agent/mock.py`), the
   LangGraph plan (`backend/app/agent/graph.py`), and/or a scenario agent in
   `agents/`. Emit render-only cards with a single `ToolCallStarted(name, args)`
   (no `ToolCallCompleted`); emit backend tools that return data with both.
4. **Store reducer** — `frontend/lib/store.ts`: add an item interface, add it to
   the `ChatItem` union, push a placeholder on `TOOL_CALL_START` for the name,
   and fill it from parsed args on `TOOL_CALL_END`.
5. **Custom component** — `frontend/components/catalog/ThingCard.tsx`, and render
   it in `frontend/components/chat/ChatArea.tsx`.
6. **CopilotKit render** — a `useCopilotAction({ name: THING_TOOL, available:
   "disabled", render })` in `frontend/components/copilot/CopilotGenerativeUI.tsx`.
   Use `renderAndWaitForResponse` only if the card collects a user response.
7. **CSS** — add any needed classes to `frontend/app/globals.css`.

Study an existing card (chart, table, or citations) before writing; copy its
shape. Human-in-the-loop cards additionally need `runId` handling — follow the
approval card.

Verify before returning:
- `cd backend && python scripts/smoke_e2e.py` (catalog parity + lint clean)
- `cd frontend && npm run typecheck && npm run build`

Return a concise summary of the files changed and the verification result. Do not
commit unless asked.
