# Start here

Before doing anything in this repository, read `AGENTS.md` (root) — it is the
canonical guide: what the project is, commands, architecture invariants, where to
add things, and gotchas. For deep context read `resources/HANDOFF.md`.

This is an AG-UI protocol demo: a FastAPI + LangGraph backend streams typed AG-UI
events over SSE; a Next.js frontend renders them with two clients (custom and
CopilotKit). Work on the `main` branch. Remaining work is in `TODO.md`.
