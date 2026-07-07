import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.db.models import PendingApproval
from app.db.session import is_initialized, session_scope
from app.logging.setup import get_logger

log = get_logger("resume")


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ApprovalDecision:
    approved: bool
    reason: str = ""

    def to_result(self) -> dict[str, Any]:
        return {"approved": self.approved, "reason": self.reason}


class ResumeRegistry:
    """Per-run HITL suspension points, durable via the database.

    An in-memory ``asyncio.Event`` wakes the awaiting run in-process, and every
    pending approval and decision is written through to the database so a decision
    is order-independent (it may arrive before or after the run suspends) and
    survives a process restart. When no database is configured (unit tests), the
    DB writes are skipped and this behaves as a pure in-memory buffer.

    Fully resuming a run's coroutine after a mid-run crash additionally needs
    graph checkpointing; here the decision channel itself is what is made durable.
    """

    def __init__(self) -> None:
        self._events: dict[str, asyncio.Event] = {}
        self._decisions: dict[str, ApprovalDecision] = {}

    def _event(self, run_id: str) -> asyncio.Event:
        event = self._events.get(run_id)
        if event is None:
            event = asyncio.Event()
            self._events[run_id] = event
        return event

    async def arm(
        self,
        run_id: str,
        *,
        thread_id: str = "",
        user_id: str = "",
        args: dict[str, Any] | None = None,
    ) -> None:
        self._event(run_id)
        await self._persist_pending(run_id, thread_id, user_id, args or {})

    async def wait(self, run_id: str) -> ApprovalDecision:
        # A decision may already be persisted: it arrived before the run suspended,
        # or was recorded by a previous process. Honor it without blocking.
        persisted = await self._load_decision(run_id)
        if persisted is not None:
            self._forget(run_id)
            return persisted

        event = self._event(run_id)
        await event.wait()
        decision = await self._load_decision(run_id)
        if decision is None:
            decision = self._decisions.get(run_id) or ApprovalDecision(
                approved=False, reason="no decision"
            )
        self._forget(run_id)
        return decision

    async def resolve(self, run_id: str, decision: ApprovalDecision) -> bool:
        self._decisions[run_id] = decision
        await self._persist_decision(run_id, decision)
        self._event(run_id).set()
        return True

    def is_waiting(self, run_id: str) -> bool:
        event = self._events.get(run_id)
        return event is not None and not event.is_set()

    def _forget(self, run_id: str) -> None:
        self._events.pop(run_id, None)
        self._decisions.pop(run_id, None)

    async def list_pending(self, user_id: str | None = None) -> list[dict[str, Any]]:
        if not is_initialized():
            return []
        try:
            async with session_scope() as session:
                stmt = select(PendingApproval).where(PendingApproval.status == "pending")
                if user_id:
                    stmt = stmt.where(PendingApproval.user_id == user_id)
                stmt = stmt.order_by(PendingApproval.created_at.desc())
                rows = (await session.execute(stmt)).scalars().all()
                return [
                    {
                        "run_id": row.run_id,
                        "thread_id": row.thread_id,
                        "args": row.args_json,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                    }
                    for row in rows
                ]
        except Exception as exc:  # noqa: BLE001
            log.warning("list_pending_failed", error=str(exc))
            return []

    async def _persist_pending(
        self, run_id: str, thread_id: str, user_id: str, args: dict[str, Any]
    ) -> None:
        if not is_initialized():
            return
        try:
            async with session_scope() as session:
                if await session.get(PendingApproval, run_id) is None:
                    session.add(
                        PendingApproval(
                            run_id=run_id,
                            thread_id=thread_id,
                            user_id=user_id,
                            args_json=args,
                            status="pending",
                        )
                    )
                    await session.commit()
        except Exception as exc:  # noqa: BLE001
            log.warning("persist_pending_failed", run_id=run_id, error=str(exc))

    async def _persist_decision(self, run_id: str, decision: ApprovalDecision) -> None:
        if not is_initialized():
            return
        try:
            async with session_scope() as session:
                row = await session.get(PendingApproval, run_id)
                if row is None:
                    row = PendingApproval(run_id=run_id, status="resolved")
                    session.add(row)
                row.status = "resolved"
                row.approved = decision.approved
                row.reason = decision.reason
                row.resolved_at = _now()
                await session.commit()
        except Exception as exc:  # noqa: BLE001
            log.warning("persist_decision_failed", run_id=run_id, error=str(exc))

    async def _load_decision(self, run_id: str) -> ApprovalDecision | None:
        if not is_initialized():
            return None
        try:
            async with session_scope() as session:
                row = await session.get(PendingApproval, run_id)
                if row is not None and row.status == "resolved":
                    return ApprovalDecision(approved=bool(row.approved), reason=row.reason or "")
        except Exception as exc:  # noqa: BLE001
            log.warning("load_decision_failed", run_id=run_id, error=str(exc))
        return None


resume_registry = ResumeRegistry()
