---
description: Check environment prerequisites (Python, Node, npm, Docker, project setup)
---

## Steps

### 1. Run the check
- From the repo root: `bash scripts/check_env.sh`

### 2. Interpret
- It verifies required tools (Python >= 3.11, Node >= 20, npm, git), optional
  tools (Docker daemon, docker compose), and project setup (`.env`,
  `backend/.venv`, `frontend/node_modules`, ports 8000/3000).
- It exits non-zero if a required prerequisite is missing or too old.

### 3. Report
- Summarize the ok / warn / fail lines. For each warning or failure, give the
  exact fix command (e.g. `cp .env.example .env`, install/upgrade the tool, or
  `cd frontend && npm install --legacy-peer-deps`).
