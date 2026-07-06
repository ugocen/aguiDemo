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
    ToolCallStarted,
)
from app.agui.catalog import (
    APPROVAL_TOOL,
    CHART_TOOL,
    FOLLOWUP_TOOL,
    FORM_TOOL,
    SUGGESTED_QUESTIONS_TOOL,
    TABLE_TOOL,
)
from app.agui.resume import ApprovalDecision

from agents._common import call_id, tokens


class TripArchitectAgent:
    """Supervising travel planner that coordinates staged specialists.

    Showcases subgraphs (Flights -> Hotels -> Experiences) plus human-in-the-loop
    approval before booking.
    """

    id = "trip-architect"
    name = "Trip Architect"
    description = "Plans a trip in stages and books on approval"
    mode = "scenario"

    system_prompt = (
        "You are a supervising travel planner. Think briefly about the trip, then "
        "work in stages: collect missing details with a renderForm, compare "
        "flight and hotel options in a renderTable, show the budget split with a "
        "renderChart, and call requestApproval before you book. Close with a "
        "renderFollowUp itinerary and renderSuggestedQuestions. Keep prose to one "
        "or two sentences."
    )
    allowed_tools = [
        FORM_TOOL,
        TABLE_TOOL,
        CHART_TOOL,
        APPROVAL_TOOL,
        FOLLOWUP_TOOL,
        SUGGESTED_QUESTIONS_TOOL,
    ]

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        dest = latest_user_text(input) or "Tokyo"

        yield StepStarted("Planning")
        yield ReasoningDelta("Sketching routes and layovers to reach the destination.")
        yield ReasoningDelta("Weighing travel dates against typical seasonal pricing.")
        yield ReasoningDelta("Balancing the budget across flights, hotel and experiences.")
        yield StepFinished("Planning")

        for token in tokens(f'Planning a trip to "{dest}".'):
            yield TextDelta(token)

        yield StepStarted("Flights")
        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=TABLE_TOOL,
            args={
                "title": "Flight options",
                "columns": ["Carrier", "Duration", "Price"],
                "rows": [
                    ["SkyLine Air", "11h 20m", "$780"],
                    ["Meridian", "13h 05m", "$640"],
                    ["Zephyr Jet", "10h 45m", "$910"],
                ],
            },
        )
        yield StepFinished("Flights")

        yield StepStarted("Budget")
        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=CHART_TOOL,
            args={
                "title": "Budget split",
                "unit": "$",
                "series": [
                    {"label": "Flights", "value": 780},
                    {"label": "Hotel", "value": 620},
                    {"label": "Experiences", "value": 400},
                ],
            },
        )
        yield StepFinished("Budget")

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=FORM_TOOL,
            args={
                "title": "Traveler details",
                "submitLabel": "Confirm details",
                "fields": [
                    {
                        "name": "email",
                        "label": "Contact email",
                        "type": "email",
                        "placeholder": "you@example.com",
                    },
                    {
                        "name": "travelers",
                        "label": "Number of travelers",
                        "type": "number",
                        "placeholder": "2",
                    },
                    {
                        "name": "dates",
                        "label": "Travel dates",
                        "type": "text",
                        "placeholder": "Sep 12 - Sep 19",
                    },
                ],
            },
        )

        decision: ApprovalDecision = yield ApprovalRequested(
            tool_call_id=call_id(),
            name=APPROVAL_TOOL,
            args={"action": "Book this itinerary", "detail": dest},
        )

        if decision.approved:
            for token in tokens(f" Booked the itinerary to {dest}. Confirmations are on the way."):
                yield TextDelta(token)
        else:
            reason = decision.reason or "no reason given"
            for token in tokens(f" Held the itinerary ({reason}); nothing was booked."):
                yield TextDelta(token)

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=FOLLOWUP_TOOL,
            args={
                "title": "Your itinerary",
                "items": [
                    {"label": "Outbound flight", "detail": "Meridian, departs 9:40 AM."},
                    {"label": "Hotel stay", "detail": "Riverside Suites, 7 nights."},
                    {"label": "Experiences", "detail": "Guided food tour and a day trip."},
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=SUGGESTED_QUESTIONS_TOOL,
            args={
                "questions": [
                    "Add travel insurance",
                    "Swap to a cheaper flight",
                    "Extend the stay",
                ],
            },
        )
