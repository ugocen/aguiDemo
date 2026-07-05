---
description: Build the deployable Docker images (backend, frontend, agentcore)
---

## Steps

Build the production/deployable artifacts. Requires a running Docker daemon.

### 1. Frontend production build (fast pre-flight)
- From `frontend/`: `npm run build` (catches type/build errors before the slower
  image build).

### 2. Build the images
- The backend and agentcore images build from the **repo root** so the `agents/`
  package is included (known gotcha):
  - `docker build -f backend/Dockerfile -t agui-demo-backend:latest .`
  - `docker build -f frontend/Dockerfile -t agui-demo-frontend:latest frontend`
  - `docker build -f deploy/agentcore/Dockerfile -t agui-demo-agent:latest .`

### 3. Report
- Report success and image sizes. If Docker is unavailable, run at least the
  frontend `npm run build` and the backend `python scripts/smoke_e2e.py`, and
  report that a Docker daemon is required for the images.
