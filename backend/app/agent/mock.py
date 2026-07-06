import uuid
from collections.abc import AsyncIterator

from ag_ui.core import RunAgentInput

from app.agent.base import latest_user_text
from app.agent.events import (
    AgentEvent,
    ApprovalRequested,
    DocumentDelta,
    ReasoningDelta,
    StepFinished,
    StepStarted,
    TextDelta,
    ToolCallCompleted,
    ToolCallStarted,
)
from app.agent.tools import lookup_knowledge
from app.agui.catalog import (
    APPROVAL_TOOL,
    FOLLOWUP_TOOL,
    LOOKUP_TOOL,
    SUGGESTED_QUESTIONS_TOOL,
    TABLE_TOOL,
)
from app.agui.resume import ApprovalDecision


def _tokens(text: str) -> list[str]:
    words = text.split(" ")
    return [w if i == 0 else " " + w for i, w in enumerate(words)]


def _call_id() -> str:
    return f"call_{uuid.uuid4().hex[:8]}"


class MockAgent:
    """Scripted agent with no external calls.

    It walks through every message type the frontend can render so the demo
    shows, in one run, how an agent sends different message types over AG-UI and
    how each is processed: streaming text, a tool call with a result, live
    canvas edits, a table, follow-up info, suggested questions, and a
    human-in-the-loop approval.
    """

    mode = "mock"

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        user_text = latest_user_text(input) or "AG-UI"

        yield StepStarted("Thinking")
        for token in _tokens(
            "The user wants an answer plus a few cards. I'll look it up, draft a note on the "
            "canvas, show a comparison table, then ask to finalize."
        ):
            yield ReasoningDelta(token)
        yield StepFinished("Thinking")

        for token in _tokens(f'You asked: "{user_text}". Let me look that up first.'):
            yield TextDelta(token)

        yield StepStarted("Looking up")
        lookup_id = _call_id()
        yield ToolCallStarted(tool_call_id=lookup_id, name=LOOKUP_TOOL, args={"query": user_text})
        result = lookup_knowledge(user_text)
        yield ToolCallCompleted(tool_call_id=lookup_id, result=result)
        yield StepFinished("Looking up")

        for token in _tokens(" I'll draft a note on the canvas as I go."):
            yield TextDelta(token)

        yield StepStarted("Rendering")

        title = f"Notes on {result.get('matched') or user_text}"
        yield DocumentDelta(patch=[{"op": "replace", "path": "/document/title", "value": title}])
        yield DocumentDelta(
            patch=[{"op": "replace", "path": "/document/content", "value": result["answer"]}]
        )

        for token in _tokens(" Here is a quick comparison table."):
            yield TextDelta(token)
        yield ToolCallStarted(
            tool_call_id=_call_id(),
            name=TABLE_TOOL,
            args={
                "title": "AG-UI event categories",
                "columns": ["Category", "Example event", "Rendered as"],
                "rows": [
                    ["Lifecycle", "RUN_STARTED", "run state"],
                    ["Text", "TEXT_MESSAGE_CONTENT", "chat bubble"],
                    ["Tool", "TOOL_CALL_START", "tool card"],
                    ["State", "STATE_DELTA", "canvas edit"],
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=_call_id(),
            name=FOLLOWUP_TOOL,
            args={
                "title": "What happens next",
                "items": [
                    {"label": "Approve to finalize", "detail": "The note is marked finalized."},
                    {"label": "Reject to keep drafting", "detail": "The note stays a draft."},
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=_call_id(),
            name=SUGGESTED_QUESTIONS_TOOL,
            args={
                "questions": [
                    "What is SSE?",
                    "Explain AgentCore",
                    "Draft a note on CopilotKit and approve",
                ]
            },
        )

        yield StepFinished("Rendering")

        approval_id = _call_id()
        decision: ApprovalDecision = yield ApprovalRequested(
            tool_call_id=approval_id,
            name=APPROVAL_TOOL,
            args={"action": "Finalize the note", "detail": title},
        )

        if decision.approved:
            yield DocumentDelta(
                patch=[
                    {
                        "op": "replace",
                        "path": "/document/content",
                        "value": result["answer"] + "\n\nStatus: finalized.",
                    }
                ]
            )
            closing = " Approved. The note is finalized."
        else:
            closing = f" Rejected ({decision.reason or 'no reason given'}). The note stays a draft."
        for token in _tokens(closing):
            yield TextDelta(token)
