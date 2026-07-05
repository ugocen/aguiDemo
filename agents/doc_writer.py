from collections.abc import AsyncIterator

from ag_ui.core import RunAgentInput

from app.agent.base import latest_user_text
from app.agent.events import (
    AgentEvent,
    ApprovalRequested,
    DocumentDelta,
    TextDelta,
    ToolCallStarted,
)
from app.agui.catalog import APPROVAL_TOOL, FOLLOWUP_TOOL
from app.agui.resume import ApprovalDecision

from agents._common import call_id, tokens


class DocWriterAgent:
    """Writing scenario, drafts a document on the canvas and asks to finalize.

    Card types exercised: streaming text, live canvas edits, follow-up list, and
    a human-in-the-loop approval before finalizing.
    """

    id = "doc-writer"
    name = "Doc Writer"
    description = "Drafts on the canvas and asks approval to finalize"
    mode = "scenario"

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        topic = latest_user_text(input) or "the topic"

        for token in tokens(f'Drafting a short note on "{topic}".'):
            yield TextDelta(token)

        title = f"Draft, {topic}"
        body = f"This note summarizes {topic}. It is a working draft you can edit."
        yield DocumentDelta(patch=[{"op": "replace", "path": "/document/title", "value": title}])
        yield DocumentDelta(patch=[{"op": "replace", "path": "/document/content", "value": body}])

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=FOLLOWUP_TOOL,
            args={
                "title": "Before you approve",
                "items": [
                    {"label": "Review the canvas", "detail": "Edit anything inline."},
                    {"label": "Approve to finalize", "detail": "Marks the note finalized."},
                ],
            },
        )

        decision: ApprovalDecision = yield ApprovalRequested(
            tool_call_id=call_id(),
            name=APPROVAL_TOOL,
            args={"action": "Finalize the draft", "detail": title},
        )

        if decision.approved:
            yield DocumentDelta(
                patch=[
                    {
                        "op": "replace",
                        "path": "/document/content",
                        "value": body + "\n\nStatus: finalized.",
                    }
                ]
            )
            closing = " Approved. The note is finalized."
        else:
            closing = f" Rejected ({decision.reason or 'no reason'}). Still a draft."
        for token in tokens(closing):
            yield TextDelta(token)
