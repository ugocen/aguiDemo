# Phase 3, EKS deployment (prepared, deployed manually later)

A minimal Helm chart for the frontend and backend. RDS PostgreSQL replaces the
local Postgres via `secrets.DATABASE_URL`, Entra sign-in is required
(`AUTH_MODE=entra`), and all endpoints come from env.

## Build and push images

Run the backend build from the repository root so the scenario agents in
`agents/` ship in the image:

```bash
docker build -f backend/Dockerfile -t <repo>/agui-demo-backend:latest .
docker build -f frontend/Dockerfile -t <repo>/agui-demo-frontend:latest frontend
docker push <repo>/agui-demo-backend:latest
docker push <repo>/agui-demo-frontend:latest
```

## Deploy

Fill `deploy/eks/values.yaml` (images, host, RDS connection string, Marketplace
and Entra values), then:

```bash
helm upgrade --install agui-demo deploy/eks -f deploy/eks/values.yaml
helm template agui-demo deploy/eks -f deploy/eks/values.yaml   # render only, to review
```

## Notes

- `DATABASE_URL` points at RDS PostgreSQL, for example
  `postgresql+asyncpg://user:pass@your-rds-host:5432/agui`.
- The ALB ingress routes `/agui`, `/conversations`, and `/agents` to the
  backend and everything else to the frontend, so SSE streams reach FastAPI
  directly. Confirm the load balancer does not buffer `text/event-stream`.
- This chart is intentionally minimal; production would add HPA, TLS, network
  policies, and per-service resource limits.
