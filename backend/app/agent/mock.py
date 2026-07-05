import uuid
from collections.abc import AsyncIterator

from ag_ui.core import RunAgentInput

from app.agent.base import latest_user_text
from app.agent.events import (
    AgentEvent,
    ApprovalRequested,
    DocumentDelta,
    TextDelta,
    ToolCallCompleted,
    ToolCallStarted,
)
from app.agent.tools import lookup_knowledge
from app.agui.catalog import LOOKUP_TOOL, APPROVAL_TOOL
from app.agui.resume import ApprovalDecision


def _tokens(text: str) -> list[str]:
    words = text.split(" ")
    return [w if i == 0 else " " + w for i, w in enumerate(words)]


class MockAgent:
    """Scripted agent with no external calls.

    It exercises all four demo capabilities in a single deterministic run so the
    UI and the event stream can be validated without the Marketplace gateway:
    streaming text, a visible tool call, a shared-state canvas edit, and a
    human-in-the-loop approval.
    """

    mode = "mock"

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        user_text = latest_user_text(input) or "AG-UI"

        intro = f'You asked: "{user_text}". Let me look that up and draft a short note.'
        for token in _tokens(intro):
            yield TextDelta(token)

        tool_call_id = f"call_{uuid.uuid4().hex[:8]}"
        yield ToolCallStarted(tool_call_id=tool_call_id, name=LOOKUP_TOOL, args={"query": user_text})
        result = lookup_knowledge(user_text)
        yield ToolCallCompleted(tool_call_id=tool_call_id, result=result)

        for token in _tokens(" Here is a draft based on what I found."):
            yield TextDelta(token)

        title = f"Notes on {result.get('matched') or user_text}"
        yield DocumentDelta(patch=[{"op": "replace", "path": "/document/title", "value": title}])
        yield DocumentDelta(
            patch=[{"op": "replace", "path": "/document/content", "value": result["answer"]}]
        )

        approval_id = f"call_{uuid.uuid4().hex[:8]}"
        decision: ApprovalDecision = yield ApprovalRequested(
            tool_call_id=approval_id,
            name=APPROVAL_TOOL,
            args={"action": "Finalize the note", "detail": title},
        )

        if decision.approved:
            closing = " Approved. The note is finalized."
            yield DocumentDelta(
                patch=[
                    {
                        "op": "replace",
                        "path": "/document/content",
                        "value": result["answer"] + "\n\nStatus: finalized.",
                    }
                ]
            )
        else:
            closing = f" Rejected ({decision.reason or 'no reason given'}). The note stays a draft."
        for token in _tokens(closing):
            yield TextDelta(token)
