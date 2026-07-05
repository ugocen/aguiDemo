---
description: Run the backend end-to-end SSE smoke test
argument-hint: (optional notes)
---

Run the backend end-to-end smoke test and report the result.

From `backend/` with the virtualenv active:

```bash
source .venv/bin/activate && python scripts/smoke_e2e.py
```

It exercises health, the agent list, every scenario agent streamed over SSE with
a resolved human-in-the-loop, an ordering-lint on each stream, the run-log
endpoint, and backend/frontend catalog parity. The last line is `SMOKE OK` or
`SMOKE FAILED`. If it fails, show the failing `[FAIL]` lines and diagnose.
$ARGUMENTS
