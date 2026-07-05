---
description: Start the backend and frontend locally for manual testing
---

Bring the app up locally so I can try it in a browser. Steps:

1. Ensure `.env` exists (`cp .env.example .env` if not). Defaults are
   `AGENT_MODE=mock`, `AUTH_MODE=dev`, `NEXT_PUBLIC_CLIENT=custom`.
2. Optional: `docker compose up -d postgres` for sidebar history.
3. Backend (background): from `backend/`, activate `.venv` (create + `pip install
   -e ".[dev]"` if missing), then `uvicorn app.main:app --reload --port 8000`.
4. Frontend (background): from `frontend/`, `npm install --legacy-peer-deps` if
   `node_modules` is missing, then `npm run dev`.
5. Confirm `curl localhost:8000/health` is ok and report the URL
   (http://localhost:3000).

To try the CopilotKit client, set `NEXT_PUBLIC_CLIENT=copilotkit` in `.env` and
restart the frontend. Run the two servers in the background so the session stays
interactive.
