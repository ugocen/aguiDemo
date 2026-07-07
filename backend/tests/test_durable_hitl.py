import pytest

from app.agui.resume import ApprovalDecision, ResumeRegistry
from app.config.settings import Settings
from app.db import session as db_session


async def _setup_db(tmp_path) -> None:
    settings = Settings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'hitl.db'}")
    db_session.init_engine(settings)
    await db_session.create_all()


async def _teardown_db() -> None:
    await db_session.dispose_engine()
    db_session._engine = None
    db_session._sessionmaker = None


@pytest.mark.asyncio
async def test_decision_survives_restart(tmp_path):
    await _setup_db(tmp_path)
    try:
        # Resolve on one registry, then a brand-new registry (a "restarted" process
        # with no in-memory event) still returns the decision from the database.
        await ResumeRegistry().resolve("run-x", ApprovalDecision(approved=True, reason="ok"))
        decision = await ResumeRegistry().wait("run-x")
        assert decision.approved is True
        assert decision.reason == "ok"
    finally:
        await _teardown_db()


@pytest.mark.asyncio
async def test_resolve_before_wait_is_order_independent(tmp_path):
    await _setup_db(tmp_path)
    try:
        reg = ResumeRegistry()
        await reg.resolve("run-y", ApprovalDecision(approved=False, reason="nope"))
        decision = await reg.wait("run-y")
        assert decision.approved is False
        assert decision.reason == "nope"
    finally:
        await _teardown_db()


@pytest.mark.asyncio
async def test_pending_listing(tmp_path):
    await _setup_db(tmp_path)
    try:
        reg = ResumeRegistry()
        await reg.arm("run-z", thread_id="t1", user_id="u1", args={"action": "Ship it"})
        pending = await reg.list_pending("u1")
        assert [p["run_id"] for p in pending] == ["run-z"]
        assert pending[0]["args"] == {"action": "Ship it"}

        await reg.resolve("run-z", ApprovalDecision(approved=True))
        assert await reg.list_pending("u1") == []
    finally:
        await _teardown_db()


@pytest.mark.asyncio
async def test_in_memory_without_db():
    # With no database configured, the registry still works as an in-memory buffer.
    assert not db_session.is_initialized()
    reg = ResumeRegistry()
    await reg.arm("run-mem")
    assert reg.is_waiting("run-mem")
    await reg.resolve("run-mem", ApprovalDecision(approved=True, reason="mem"))
    decision = await reg.wait("run-mem")
    assert decision.approved is True
    assert decision.reason == "mem"
