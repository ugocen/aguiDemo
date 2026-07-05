---
description: Verify the repo end to end (backend tests + smoke, frontend typecheck/lint/build)
---

Verify the AG-UI demo is healthy. Prefer launching the `agui-verifier` subagent
so the checks run and report in one place. It should run, from the backend venv,
`pytest -q` and `python scripts/smoke_e2e.py`, and from `frontend/`,
`npm run typecheck && npm run lint && npm run build` (running
`npm install --legacy-peer-deps` first if `node_modules` is missing).

Report a compact pass/fail table and an overall verdict. Do not change code as
part of verifying — surface failures instead.
