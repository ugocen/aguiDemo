import asyncio
from dataclasses import dataclass
from typing import Any


@dataclass
class ApprovalDecision:
    approved: bool
    reason: str = ""

    def to_result(self) -> dict[str, Any]:
        return {"approved": self.approved, "reason": self.reason}


class ResumeRegistry:
    """In-memory per-run suspension points, keyed by run_id.

    A decision may arrive before or after the run reaches its suspend point, so
    both the waiter and the resolver create the event lazily and the decision is
    buffered until consumed. A production system would back this with a durable
    workflow engine so a suspended run survives a process restart. That is
    intentionally out of scope for this demo, and Temporal is deliberately not
    used here.
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

    def arm(self, run_id: str) -> None:
        self._event(run_id)

    async def wait(self, run_id: str) -> ApprovalDecision:
        event = self._event(run_id)
        await event.wait()
        decision = self._decisions.pop(run_id, ApprovalDecision(approved=False, reason="no decision"))
        self._events.pop(run_id, None)
        return decision

    def resolve(self, run_id: str, decision: ApprovalDecision) -> bool:
        self._decisions[run_id] = decision
        self._event(run_id).set()
        return True

    def is_waiting(self, run_id: str) -> bool:
        event = self._events.get(run_id)
        return event is not None and not event.is_set()


resume_registry = ResumeRegistry()
