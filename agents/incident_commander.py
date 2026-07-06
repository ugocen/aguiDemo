from collections.abc import AsyncIterator

from ag_ui.core import RunAgentInput

from app.agent.base import latest_user_text
from app.agent.events import (
    AgentEvent,
    ApprovalRequested,
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
    CHART_TOOL,
    FOLLOWUP_TOOL,
    LOOKUP_TOOL,
    TABLE_TOOL,
)
from app.agui.resume import ApprovalDecision
from agents._common import call_id, tokens


class IncidentCommanderAgent:
    """Works an incident live from detection to postmortem.

    Showcases agentic_generative_ui long-running status plus human-in-the-loop.
    """

    id = "incident-commander"
    name = "Incident Commander"
    description = "Runs a live incident runbook and rolls back on approval"
    mode = "scenario"

    system_prompt = (
        "You are an incident commander working an incident live: think through the "
        "signal, then move through Detect, Diagnose, Remediate and Verify. Look up "
        "the runbook with lookupKnowledge, show affected services in a renderTable, "
        "chart impact with renderChart, and call requestApproval before any rollback. "
        "Finish with a renderFollowUp postmortem. Keep prose to one or two sentences."
    )
    allowed_tools = [LOOKUP_TOOL, TABLE_TOOL, CHART_TOOL, APPROVAL_TOOL, FOLLOWUP_TOOL]

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        signal = latest_user_text(input) or "elevated 5xx errors"

        yield StepStarted("Detect")
        yield ReasoningDelta(f"A page just fired for {signal}.")
        yield ReasoningDelta("Confirming the alert is real before I declare an incident.")
        for token in tokens(f'Investigating "{signal}".'):
            yield TextDelta(token)
        yield StepFinished("Detect")

        yield StepStarted("Diagnose")
        lid = call_id()
        yield ToolCallStarted(tool_call_id=lid, name=LOOKUP_TOOL, args={"query": signal})
        result = lookup_knowledge(signal)
        yield ToolCallCompleted(tool_call_id=lid, result=result)
        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=TABLE_TOOL,
            args={
                "title": "Affected services",
                "columns": ["Service", "Status", "Error rate"],
                "rows": [
                    ["checkout-api", "Degraded", "12.4%"],
                    ["payments", "Degraded", "8.1%"],
                    ["notifications", "Healthy", "0.3%"],
                ],
            },
        )
        yield StepFinished("Diagnose")

        yield StepStarted("Assess")
        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=CHART_TOOL,
            args={
                "title": "Impact by service",
                "unit": "%",
                "series": [
                    {"label": "checkout-api", "value": 12.4},
                    {"label": "payments", "value": 8.1},
                    {"label": "notifications", "value": 0.3},
                ],
            },
        )
        yield StepFinished("Assess")

        decision: ApprovalDecision = yield ApprovalRequested(
            tool_call_id=call_id(),
            name=APPROVAL_TOOL,
            args={"action": "Roll back to the previous release", "detail": signal},
        )

        yield StepStarted("Remediate")
        if decision.approved:
            for token in tokens("Rolling back to the previous release now."):
                yield TextDelta(token)
        else:
            reason = decision.reason or "no reason given"
            for token in tokens(f"Holding the current release ({reason}) and watching the signal."):
                yield TextDelta(token)
        yield StepFinished("Remediate")

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=FOLLOWUP_TOOL,
            args={
                "title": "Postmortem",
                "items": [
                    {
                        "label": "Root cause",
                        "detail": f"Trace the regression behind {signal} to the last deploy.",
                    },
                    {
                        "label": "Follow-up",
                        "detail": "Add an alert and a canary gate to catch this earlier.",
                    },
                ],
            },
        )
