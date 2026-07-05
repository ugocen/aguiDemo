---
description: Start the backend and frontend locally for manual testing
---

## Steps

### 1. Env
- Ensure `.env` exists (`cp .env.example .env` if not). Defaults: `AGENT_MODE=mock`,
  `AUTH_MODE=dev`, `NEXT_PUBLIC_CLIENT=custom`.

### 2. Postgres (optional, for sidebar history)
- `docker compose up -d postgres`

### 3. Backend (background)
- From `backend/`, activate `.venv` (create + `pip install -e ".[dev]"` if missing).
- `uvicorn app.main:app --reload --port 8000`
- Confirm `curl localhost:8000/health` is ok.

### 4. Frontend (background)
- From `frontend/`, `npm install --legacy-peer-deps` if `node_modules` is missing.
- `npm run dev` → http://localhost:3000

### 5. Try the CopilotKit client
- Set `NEXT_PUBLIC_CLIENT=copilotkit` in `.env` and restart the frontend.
