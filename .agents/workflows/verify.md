---
description: Verify the repo end to end (backend tests + smoke, frontend typecheck/lint/build)
---

## Steps

### 1. Backend tests
- From `backend/`, activate the venv (`source .venv/bin/activate`; create it and
  `pip install -e ".[dev]"` if missing).
- Run `pytest -q`. Expect 4 passed.

### 2. Backend end-to-end smoke
- Run `python scripts/smoke_e2e.py`.
- It checks health, the agent list, every scenario streamed over SSE with a
  resolved human-in-the-loop, an ordering-lint per stream, the run-log endpoint,
  and backend/frontend catalog parity. The last line is `SMOKE OK` or `SMOKE FAILED`.

### 3. Frontend
- From `frontend/`, run `npm install --legacy-peer-deps` if `node_modules` is
  missing, then `npm run typecheck && npm run lint && npm run build`.

### 4. Report
- Report a compact pass/fail table with the exact error lines for any failure.
  Do not change code as part of verifying — surface failures instead.
