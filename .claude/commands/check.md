---
description: Check environment prerequisites (Python, Node, npm, Docker, project setup)
---

Run the environment / prerequisites check and report the result:

```bash
bash scripts/check_env.sh
```

It verifies the required tools (Python >= 3.11, Node >= 20, npm, git) and the
optional ones (Docker daemon, docker compose), plus project setup (`.env`,
`backend/.venv`, `frontend/node_modules`, ports 8000/3000). It exits non-zero if
a required prerequisite is missing or too old.

Summarize the ok/warn/fail lines and, for any warning or failure, give the exact
command to fix it (e.g. `cp .env.example .env`, install/upgrade a tool, or
`npm install --legacy-peer-deps`).
