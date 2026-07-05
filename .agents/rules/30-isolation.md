# Never install globally — always isolate

Do not install dependencies globally or on the host under any circumstances.
Always use an isolated environment:

- **Python** → a virtualenv at `backend/.venv`. Create it if missing
  (`python -m venv backend/.venv && source backend/.venv/bin/activate &&
  pip install -e "backend[dev]"`). Never `sudo pip`, `pip install --user`, or a
  bare global `pip install`.
- **Node** → the project-local `frontend/node_modules`
  (`cd frontend && npm install --legacy-peer-deps`). Never `npm install -g`.
- **Services** (Postgres, etc.) → Docker (`docker compose up -d postgres`), never
  a host install.

No `sudo`. If an isolated environment does not exist yet, create it first, then
install into it. Run `bash scripts/check_env.sh` (or `/check`) to see what is
present.
