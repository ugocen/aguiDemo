---
description: Add a new AG-UI card/message type end to end
---

## Steps

Add a new AG-UI card/message type across the backend catalog, an agent that emits
it, and both frontend clients. Study an existing card (chart, table, or citations)
and copy its shape. For a type named `renderThing`:

### 1. Catalogs (keep in sync)
- `backend/app/agui/catalog.py`: add a `THING_TOOL` constant and a schema entry in
  `tool_catalog()`.
- `frontend/lib/catalog.ts`: mirror the constant and schema exactly (same name,
  same required fields).

### 2. Emit it
- From an agent (`backend/app/agent/mock.py`, `backend/app/agent/graph.py`, or a
  scenario in `agents/`): render-only cards use a single `ToolCallStarted(name,
  args)`; backend tools that return data use `ToolCallStarted` + `ToolCallCompleted`.

### 3. Custom client
- `frontend/lib/store.ts`: add an item interface, add it to `ChatItem`, push a
  placeholder on `TOOL_CALL_START`, fill it from args on `TOOL_CALL_END`.
- Add `frontend/components/catalog/ThingCard.tsx` and render it in
  `frontend/components/chat/ChatArea.tsx`. Add CSS to `frontend/app/globals.css`.

### 4. CopilotKit client
- Add a `useCopilotAction({ name: THING_TOOL, available: "disabled", render })` in
  `frontend/components/copilot/CopilotGenerativeUI.tsx`
  (`renderAndWaitForResponse` if it collects a user response).

### 5. Verify
- `cd backend && python scripts/smoke_e2e.py` (catalog parity + lint clean) and
  `cd frontend && npm run typecheck && npm run build`.
