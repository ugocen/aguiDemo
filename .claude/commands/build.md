---
description: Build the deployable Docker images (backend, frontend, agentcore)
argument-hint: (optional image tag, default latest)
---

Build the production/deployable artifacts for this repo. Requires a running
Docker daemon.

1. Frontend production build as a fast pre-flight (catches type/build errors
   before the slower image build): from `frontend/`, `npm run build`.
2. Build the images. The backend and agentcore images build from the **repo
   root** so the `agents/` package is included (this is a known gotcha):
   - `docker build -f backend/Dockerfile -t agui-demo-backend:latest .`
   - `docker build -f frontend/Dockerfile -t agui-demo-frontend:latest frontend`
   - `docker build -f deploy/agentcore/Dockerfile -t agui-demo-agent:latest .`
3. Report success and image sizes.

If Docker is unavailable, run at least the frontend `npm run build` and the
backend `python scripts/smoke_e2e.py`, and report that a Docker daemon is
required to build the images. $ARGUMENTS
