#!/usr/bin/env bash
# AG-UI Demo — environment / prerequisites check.
# Verifies the tools and project setup needed to run and build the demo.
# Exits non-zero if a REQUIRED prerequisite is missing or too old.

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ok=0
warn=0
fail=0

green() { printf '\033[32m%s\033[0m' "$1"; }
yellow() { printf '\033[33m%s\033[0m' "$1"; }
red() { printf '\033[31m%s\033[0m' "$1"; }

pass() { printf '  [%s] %s\n' "$(green ok)" "$1"; ok=$((ok + 1)); }
warning() { printf '  [%s] %s\n' "$(yellow warn)" "$1"; warn=$((warn + 1)); }
error() { printf '  [%s] %s\n' "$(red FAIL)" "$1"; fail=$((fail + 1)); }

# ver_ge A B -> success if version A >= B (dotted numeric)
ver_ge() {
  [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

num() { printf '%s' "$1" | grep -oE '[0-9]+(\.[0-9]+)*' | head -n1; }

echo "AG-UI Demo — environment check"
echo "repo: $REPO_ROOT"
echo
echo "Required:"

# Python >= 3.11
if command -v python3 >/dev/null 2>&1; then
  PY="$(python3 -c 'import sys;print("%d.%d.%d"%sys.version_info[:3])' 2>/dev/null)"
  if ver_ge "$PY" "3.11"; then pass "Python $PY  (need >= 3.11)"; else error "Python $PY is too old (need >= 3.11)"; fi
else
  error "Python 3 not found (need >= 3.11)"
fi

# Node >= 20
if command -v node >/dev/null 2>&1; then
  NODE="$(num "$(node -v)")"
  if ver_ge "$NODE" "20"; then pass "Node v$NODE  (need >= 20)"; else error "Node v$NODE is too old (need >= 20)"; fi
else
  error "Node not found (need >= 20)"
fi

# npm
if command -v npm >/dev/null 2>&1; then pass "npm $(npm -v)"; else error "npm not found"; fi

# git
if command -v git >/dev/null 2>&1; then pass "git $(num "$(git --version)")"; else error "git not found"; fi

echo
echo "Optional (for local Postgres and image builds):"

# Docker
if command -v docker >/dev/null 2>&1; then
  DVER="$(num "$(docker --version 2>/dev/null)")"
  if docker info >/dev/null 2>&1; then pass "Docker $DVER (daemon running)"; else warning "Docker $DVER installed but daemon not reachable"; fi
else
  warning "Docker not found (needed for local Postgres and 'npm'-free builds)"
fi

# docker compose (v2 plugin or legacy)
if docker compose version >/dev/null 2>&1; then pass "docker compose $(num "$(docker compose version 2>/dev/null)")"; \
elif command -v docker-compose >/dev/null 2>&1; then pass "docker-compose $(num "$(docker-compose --version 2>/dev/null)")"; \
else warning "docker compose not found (needed for the local Postgres in docker-compose.yml)"; fi

echo
echo "Project setup:"

# .env
if [ -f "$REPO_ROOT/.env" ]; then pass ".env present"; else warning ".env missing (run: cp .env.example .env)"; fi

# backend venv
if [ -d "$REPO_ROOT/backend/.venv" ]; then pass "backend/.venv present"; else warning "backend/.venv missing (python -m venv backend/.venv && pip install -e 'backend[dev]')"; fi

# frontend deps
if [ -d "$REPO_ROOT/frontend/node_modules" ]; then pass "frontend/node_modules present"; else warning "frontend deps missing (cd frontend && npm install --legacy-peer-deps)"; fi

# ports
for port in 8000 3000; do
  if command -v lsof >/dev/null 2>&1 && lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    warning "port $port is in use (backend=8000, frontend=3000)"
  fi
done

echo
printf 'Summary: %s ok, %s warning(s), %s failure(s)\n' "$(green "$ok")" "$(yellow "$warn")" "$(red "$fail")"
if [ "$fail" -gt 0 ]; then
  echo "Result: FAIL — install/upgrade the required tools above."
  exit 1
fi
echo "Result: OK — required prerequisites satisfied."
