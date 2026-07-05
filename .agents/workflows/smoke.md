---
description: Run the backend end-to-end SSE smoke test
---

## Steps

### 1. Run the smoke
- From `backend/` with the venv active:
  `source .venv/bin/activate && python scripts/smoke_e2e.py`

### 2. Interpret
- It exercises health, the agent list, every scenario agent streamed over SSE
  with a resolved human-in-the-loop, an ordering-lint per stream, the run-log
  endpoint, and backend/frontend catalog parity.
- The last line is `SMOKE OK` (exit 0) or `SMOKE FAILED` (exit 1).
- On failure, show the `[FAIL]` lines and diagnose the root cause.
