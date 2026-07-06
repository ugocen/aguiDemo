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
    ToolCallStarted,
)
from app.agui.catalog import APPROVAL_TOOL, FOLLOWUP_TOOL
from app.agui.resume import ApprovalDecision
from agents._common import call_id, tokens


class ContentStudioAgent:
    """Drafts copy on a live canvas and publishes on approval.

    Showcases predictive_state_updates: streamed document edits to a canvas.
    """

    id = "content-studio"
    name = "Content Studio"
    description = "Drafts on the canvas live and publishes on approval"
    mode = "scenario"

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        topic = latest_user_text(input) or "the launch note"

        yield StepStarted("Drafting")
        yield ReasoningDelta("Outlining the note and picking the key points to lead with.")
        yield ReasoningDelta("Tightening the copy so every sentence earns its place.")
        yield StepFinished("Drafting")

        for token in tokens(f'Drafting a note on "{topic}".'):
            yield TextDelta(token)

        title = f"Launch note: {topic}"
        yield DocumentDelta(
            patch=[{"op": "replace", "path": "/document/title", "value": title}]
        )

        initial = (
            f"We are excited to share an update on {topic}. "
            "Here is a quick first pass at the announcement."
        )
        yield DocumentDelta(
            patch=[{"op": "replace", "path": "/document/content", "value": initial}]
        )

        revised = (
            f"We are excited to share an update on {topic}. "
            "This release brings the improvements our team has been working toward, "
            "and we think you will notice the difference right away. "
            "Read on for what changed and why it matters."
        )
        yield DocumentDelta(
            patch=[{"op": "replace", "path": "/document/content", "value": revised}]
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=FOLLOWUP_TOOL,
            args={
                "title": "Before you publish",
                "items": [
                    {
                        "label": "Check the tone",
                        "detail": "Make sure the voice matches the brand style guide.",
                    },
                    {
                        "label": "Confirm the timing",
                        "detail": "Verify the publish window aligns with the launch plan.",
                    },
                ],
            },
        )

        decision: ApprovalDecision = yield ApprovalRequested(
            tool_call_id=call_id(),
            name=APPROVAL_TOOL,
            args={"action": "Publish the draft", "detail": title},
        )

        if decision.approved:
            published = f"{revised}\n\nStatus: Published."
            yield DocumentDelta(
                patch=[
                    {"op": "replace", "path": "/document/content", "value": published}
                ]
            )
            for token in tokens("Published."):
                yield TextDelta(token)
        else:
            reason = decision.reason or "no reason given"
            for token in tokens(f"Kept as a draft ({reason})."):
                yield TextDelta(token)
