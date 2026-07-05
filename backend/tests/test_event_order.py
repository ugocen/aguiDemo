import asyncio

import pytest
from ag_ui.core import RunAgentInput, UserMessage

from app.agent.mock import MockAgent
from app.agui.lint import lint_event_stream
from app.agui.resume import ApprovalDecision, resume_registry
from app.agui.translator import Translator


def _make_input(run_id: str, text: str) -> RunAgentInput:
    return RunAgentInput(
        thread_id="thread-test",
        run_id=run_id,
        state={},
        messages=[UserMessage(id="u1", role="user", content=text)],
        tools=[],
        context=[],
        forwarded_props={},
    )


async def _collect(translator: Translator, run_id: str, approve: bool) -> list[dict]:
    events: list[dict] = []

    async def resolver() -> None:
        for _ in range(200):
            if resume_registry.is_waiting(run_id):
                resume_registry.resolve(run_id, ApprovalDecision(approved=approve, reason="test"))
                return
            await asyncio.sleep(0.01)

    resolver_task = asyncio.create_task(resolver())
    async for event in translator.stream():
        events.append(event.model_dump(by_alias=True, exclude_none=True))
    await resolver_task
    return events


@pytest.mark.asyncio
async def test_mock_run_event_stream_is_well_formed():
    run_id = "run-approve"
    translator = Translator(input=_make_input(run_id, "explain ag-ui"), agent=MockAgent(), user_id="tester")
    events = await _collect(translator, run_id, approve=True)

    problems = lint_event_stream(events)
    assert problems == [], problems

    types = [e["type"] for e in events]
    assert types[0] == "RUN_STARTED"
    assert types[1] == "STATE_SNAPSHOT"
    assert types[-1] == "RUN_FINISHED"
    assert "TOOL_CALL_START" in types
    assert "TOOL_CALL_RESULT" in types
    assert "STATE_DELTA" in types


@pytest.mark.asyncio
async def test_reject_path_still_well_formed():
    run_id = "run-reject"
    translator = Translator(input=_make_input(run_id, "explain sse"), agent=MockAgent(), user_id="tester")
    events = await _collect(translator, run_id, approve=False)

    assert lint_event_stream(events) == []
    assert translator.result.assistant_text != ""


def test_linter_flags_missing_run_started():
    bad = [{"type": "TEXT_MESSAGE_START", "messageId": "m1"}]
    problems = lint_event_stream(bad)
    assert any("RUN_STARTED" in p for p in problems)


def test_linter_flags_unbalanced_text():
    bad = [
        {"type": "RUN_STARTED"},
        {"type": "TEXT_MESSAGE_START", "messageId": "m1"},
        {"type": "RUN_FINISHED"},
    ]
    problems = lint_event_stream(bad)
    assert any("left open" in p for p in problems)
