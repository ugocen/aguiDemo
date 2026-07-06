"""End-to-end smoke test for the AG-UI backend.

Drives the FastAPI app in-process over ASGI (no server, no Postgres needed):
health, agent list, every scenario agent streamed over SSE with a resolved
human-in-the-loop, ordering-lint on each stream, the run-log endpoint, and
backend/frontend tool-catalog parity. Exits non-zero on any failure so it can
gate CI or a /smoke command.

Run from the backend directory with the venv active:
    python scripts/smoke_e2e.py
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

os.environ.setdefault("LOG_LEVEL", "critical")
os.environ.setdefault("AGENT_MODE", "mock")
logging.disable(logging.CRITICAL)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(REPO_ROOT))

import httpx  # noqa: E402
import structlog  # noqa: E402
from httpx import ASGITransport  # noqa: E402

structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL))

from app.agui.lint import lint_event_stream  # noqa: E402
from app.agui.resume import ApprovalDecision, resume_registry  # noqa: E402
from app.main import app  # noqa: E402

failures: list[str] = []


def check(condition: bool, label: str) -> None:
    status = "ok" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        failures.append(label)


async def run_stream(client: httpx.AsyncClient, agent_id: str | None, run_id: str) -> list[dict]:
    async def resolver() -> None:
        for _ in range(500):
            if resume_registry.is_waiting(run_id):
                await client.post(
                    "/agui/resume", json={"run_id": run_id, "approved": True, "reason": "smoke"}
                )
                return
            await asyncio.sleep(0.02)

    task = asyncio.create_task(resolver())
    body = {
        "threadId": f"t-{run_id}",
        "runId": run_id,
        "state": {},
        "messages": [{"id": "u1", "role": "user", "content": "explain ag-ui and draft a note then approve"}],
        "tools": [],
        "context": [],
        "forwardedProps": {"agentId": agent_id} if agent_id else {},
    }
    events: list[dict] = []
    async with client.stream("POST", "/agui/run", json=body) as response:
        check(response.status_code == 200, f"{run_id}: 200")
        check(
            response.headers.get("content-type", "").startswith("text/event-stream"),
            f"{run_id}: SSE content-type",
        )
        check(response.headers.get("x-accel-buffering") == "no", f"{run_id}: X-Accel-Buffering")
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[5:]))
    await task
    return events


def check_catalog_parity() -> None:
    from app.agui.catalog import tool_catalog

    backend = {t["name"] for t in tool_catalog()}
    ts = (REPO_ROOT / "frontend" / "lib" / "catalog.ts").read_text()
    import re

    frontend = set(re.findall(r'export const \w+_TOOL = "(\w+)"', ts))
    check(backend == frontend, f"catalog parity ({len(backend)} tools)")
    if backend != frontend:
        print("    backend-only:", backend - frontend, "frontend-only:", frontend - backend)


async def main() -> None:
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=60) as c:
            print("health / agents:")
            health = await c.get("/health")
            check(health.status_code == 200, "GET /health")
            agents = await c.get("/agents")
            ids = [a["id"] for a in agents.json()]
            expected = ["research-assistant", "doc-writer", "data-analyst", "support-triage"]
            check(ids == expected, f"GET /agents = {expected}")

            print("scenario streams:")
            for agent_id in [None, *expected]:
                run_id = agent_id or "mock-default"
                events = await run_stream(c, agent_id, run_id)
                problems = lint_event_stream(events)
                check(not problems, f"{run_id}: lint clean")
                if problems:
                    print("    problems:", problems)

            print("run log:")
            log = await c.get("/agui/runs/data-analyst/log")
            captured = log.json()["events"]
            check(len(captured) > 0 and not lint_event_stream(captured), "run-log lints clean")

            print("catalog:")
            check_catalog_parity()


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(main(), 120))
    if failures:
        print(f"\nSMOKE FAILED: {len(failures)} check(s) failed")
        sys.exit(1)
    print("\nSMOKE OK")
