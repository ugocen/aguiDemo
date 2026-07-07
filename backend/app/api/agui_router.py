import asyncio
from collections.abc import AsyncIterator

from ag_ui.core import RunAgentInput
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent.base import latest_user_text
from app.agent.factory import build_agent
from app.agui.resume import ApprovalDecision, resume_registry
from app.agui.run_capture import RunCapture, list_run_logs, load_run_log
from app.agui.translator import RunResult, Translator
from app.auth.entra import Principal, get_current_principal
from app.config.settings import Settings, get_settings
from app.db.repository import SqlAlchemyHistoryRepository
from app.db.session import session_scope
from app.logging.setup import get_logger

router = APIRouter(tags=["agui"])
log = get_logger("agui_router")

KEEPALIVE_INTERVAL_SECONDS = 15.0


class ResumeIn(BaseModel):
    run_id: str
    approved: bool
    reason: str = ""


async def _persist_user_turn(thread_id: str, user_id: str, text: str) -> None:
    if not text:
        return
    try:
        async with session_scope() as session:
            repo = SqlAlchemyHistoryRepository(session)
            conversation = await repo.get_conversation(user_id, thread_id)
            if conversation is None:
                return
            await repo.add_message(thread_id, "user", text)
            title = conversation.title
            if title in ("", "New conversation"):
                title = text[:60]
            await repo.touch_conversation(thread_id, title=title)
    except Exception as exc:  # noqa: BLE001
        log.warning("persist_user_failed", error=str(exc))


async def _persist_assistant_turn(thread_id: str, user_id: str, result: RunResult) -> None:
    if result.errored:
        return
    try:
        async with session_scope() as session:
            repo = SqlAlchemyHistoryRepository(session)
            conversation = await repo.get_conversation(user_id, thread_id)
            if conversation is None:
                return
            await repo.add_message(
                thread_id,
                "assistant",
                result.assistant_text,
                tool_events=result.tool_events or None,
            )
            await repo.touch_conversation(thread_id)
    except Exception as exc:  # noqa: BLE001
        log.warning("persist_assistant_failed", error=str(exc))


async def _sse_with_keepalive(
    events: AsyncIterator, encoder: EventEncoder
) -> AsyncIterator[str]:
    queue: asyncio.Queue = asyncio.Queue()
    sentinel = object()

    async def pump() -> None:
        try:
            async for event in events:
                await queue.put(event)
        except Exception as exc:  # noqa: BLE001
            await queue.put(exc)
        finally:
            await queue.put(sentinel)

    task = asyncio.create_task(pump())
    try:
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
                continue
            if item is sentinel:
                break
            if isinstance(item, Exception):
                raise item
            yield encoder.encode(item)
    finally:
        task.cancel()


@router.post("/agui/run")
async def run_agent(
    input: RunAgentInput,
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    encoder = EventEncoder()
    forwarded = input.forwarded_props if isinstance(input.forwarded_props, dict) else {}
    agent = build_agent(settings, agent_id=forwarded.get("agentId"))
    capture = RunCapture(input.run_id, input.thread_id, principal.user_id)
    translator = Translator(
        input=input, agent=agent, user_id=principal.user_id, capture=capture
    )

    await _persist_user_turn(input.thread_id, principal.user_id, latest_user_text(input))

    async def body() -> AsyncIterator[str]:
        async for chunk in _sse_with_keepalive(translator.stream(), encoder):
            yield chunk
        await _persist_assistant_turn(input.thread_id, principal.user_id, translator.result)

    return StreamingResponse(
        body(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/agui/resume")
async def resume_run(
    body: ResumeIn,
    _principal: Principal = Depends(get_current_principal),
) -> dict:
    decision = ApprovalDecision(approved=body.approved, reason=body.reason)
    resolved = await resume_registry.resolve(body.run_id, decision)
    return {"resolved": resolved, "run_id": body.run_id}


@router.get("/agui/approvals")
async def list_approvals(
    principal: Principal = Depends(get_current_principal),
) -> dict:
    """Durable pending human-in-the-loop approvals for the caller."""
    return {"pending": await resume_registry.list_pending(principal.user_id)}


@router.get("/agui/runs")
async def list_runs(
    _principal: Principal = Depends(get_current_principal),
) -> dict:
    """Summaries of captured runs, newest first, for the replay dashboard."""
    return {"runs": list_run_logs()}


@router.get("/agui/runs/{run_id}/log")
async def get_run_log(
    run_id: str,
    _principal: Principal = Depends(get_current_principal),
) -> dict:
    return {"run_id": run_id, "events": load_run_log(run_id)}
