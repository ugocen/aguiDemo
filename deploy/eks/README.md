# Phase 3, EKS deployment (prepared, deployed manually later)

A minimal Helm chart for the frontend and backend. RDS PostgreSQL replaces the
local Postgres via `secrets.DATABASE_URL`, Entra sign-in is required
(`AUTH_MODE=entra`), and all endpoints come from env.

## Build and push images

Run the backend build from the repository root so the scenario agents in
`agents/` ship in the image. **EKS nodes are `amd64`** — build with
`--platform linux/amd64` (an arm64 image crashes pods with `exec format error`).
The frontend inlines `NEXT_PUBLIC_*` at build time; the Dockerfile defaults
`NEXT_PUBLIC_BACKEND_URL` to same-origin (`""`) so the browser reaches the backend
through the ALB path routing — override with `--build-arg` for a custom setup.

```bash
docker build --platform linux/amd64 -f backend/Dockerfile -t <repo>/agui-demo-backend:latest .
docker build --platform linux/amd64 -f frontend/Dockerfile -t <repo>/agui-demo-frontend:latest frontend
docker push <repo>/agui-demo-backend:latest
docker push <repo>/agui-demo-frontend:latest
```

## Deploy

Credentials are managed **out-of-band** so they never enter Helm values/history:
leave `secrets: {}` in values (the chart then skips its Secret) and create the
`<release>-secrets` Secret yourself with the keys the app needs
(`DATABASE_URL`, `GEMINI_API_KEY` or `MARKETPLACE_*`, `ENTRA_*` when
`AUTH_MODE=entra`):

```bash
kubectl create secret generic agui-demo-secrets --from-env-file=secrets.env
```

Fill `deploy/eks/values.yaml` (images, host, env), then:

```bash
helm upgrade --install agui-demo deploy/eks -f deploy/eks/values.yaml
helm template agui-demo deploy/eks -f deploy/eks/values.yaml   # render only, to review
```

Access the app at the ALB DNS name (`kubectl get ingress`); `host: ""` in values
makes the ingress match any host so the ALB DNS works without a custom domain.

## Notes

- `DATABASE_URL` points at RDS PostgreSQL, for example
  `postgresql+asyncpg://user:pass@your-rds-host:5432/agui`.
- The ALB ingress routes `/agui`, `/conversations`, and `/agents` to the
  backend and everything else to the frontend, so SSE streams reach FastAPI
  directly. Confirm the load balancer does not buffer `text/event-stream`.
- This chart is intentionally minimal; production would add HPA, TLS, network
  policies, and per-service resource limits.
