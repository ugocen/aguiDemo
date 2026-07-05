# Always verify after changes

After any code change, verify before considering the work done (or run the
`/verify` workflow):

- Backend (from `backend/`, venv active): `pytest -q` and
  `python scripts/smoke_e2e.py`. The smoke exits non-zero on failure; its last
  line is `SMOKE OK` or `SMOKE FAILED`.
- Frontend (from `frontend/`): `npm run typecheck && npm run lint && npm run build`.
  If `node_modules` is missing, run `npm install --legacy-peer-deps` first.

Do not report a change as complete while any of these fail.
