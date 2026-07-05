from collections.abc import AsyncIterator

from ag_ui.core import RunAgentInput

from app.agent.base import latest_user_text
from app.agent.events import (
    AgentEvent,
    ApprovalRequested,
    TextDelta,
    ToolCallCompleted,
    ToolCallStarted,
)
from app.agent.tools import lookup_knowledge
from app.agui.catalog import APPROVAL_TOOL, FOLLOWUP_TOOL, LOOKUP_TOOL
from app.agui.resume import ApprovalDecision

from agents._common import call_id, tokens


class SupportTriageAgent:
    """Support scenario, finds an answer then asks approval before escalating.

    Card types exercised: streaming text, lookup tool card, a human-in-the-loop
    approval to escalate, and a follow-up resolution list.
    """

    id = "support-triage"
    name = "Support Triage"
    description = "Finds an answer and asks approval before escalating"
    mode = "scenario"

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        issue = latest_user_text(input) or "the issue"

        for token in tokens(f'Triaging "{issue}". Checking the knowledge base.'):
            yield TextDelta(token)

        lookup = call_id()
        yield ToolCallStarted(tool_call_id=lookup, name=LOOKUP_TOOL, args={"query": issue})
        result = lookup_knowledge(issue)
        yield ToolCallCompleted(tool_call_id=lookup, result=result)

        decision: ApprovalDecision = yield ApprovalRequested(
            tool_call_id=call_id(),
            name=APPROVAL_TOOL,
            args={"action": "Escalate to a human agent", "detail": issue},
        )

        if decision.approved:
            for token in tokens(" Escalated. A human agent will follow up."):
                yield TextDelta(token)
        else:
            for token in tokens(" Not escalated. Sharing self-serve steps."):
                yield TextDelta(token)

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=FOLLOWUP_TOOL,
            args={
                "title": "Resolution steps",
                "items": [
                    {"label": "Check the docs", "detail": result["answer"][:60] + "..."},
                    {"label": "Reply to confirm", "detail": "Close the ticket when resolved."},
                ],
            },
        )
