from collections.abc import AsyncIterator

from ag_ui.core import RunAgentInput

from app.agent.base import latest_user_text
from app.agent.events import (
    AgentEvent,
    ApprovalRequested,
    ReasoningDelta,
    StateDelta,
    StepFinished,
    StepStarted,
    TextDelta,
    ToolCallStarted,
)
from app.agui.catalog import (
    APPROVAL_TOOL,
    DATE_PICKER_TOOL,
    HOTELS_TOOL,
    SUGGESTED_QUESTIONS_TOOL,
    TABLE_TOOL,
)
from app.agui.resume import ApprovalDecision

from agents._common import call_id, tokens


class TravelConciergeAgent:
    """Turkey-market booking concierge that searches hotels and builds a cart.

    Showcases tool-based generative UI plus shared state via a live booking cart.
    """

    id = "travel-concierge"
    name = "Travel Concierge"
    description = "Finds Turkey hotels and builds a booking cart"
    mode = "scenario"

    system_prompt = (
        "You are a Turkey-market OTA booking concierge. Search hotels and respect "
        "local regulation by listing only TURSAB-licensed hotels, render clickable "
        "hotel cards with renderHotels and a renderDatePicker, keep the shared "
        "booking cart in sync as the traveler chooses, and call requestApproval "
        "before booking. Keep prose to one or two sentences."
    )
    allowed_tools = [
        HOTELS_TOOL,
        DATE_PICKER_TOOL,
        TABLE_TOOL,
        APPROVAL_TOOL,
        SUGGESTED_QUESTIONS_TOOL,
    ]

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        dest = latest_user_text(input) or "Antalya"
        state = input.state if isinstance(input.state, dict) else {}
        cart = state.get("cart") or {}
        nights = cart.get("nights") or 5

        yield StepStarted("Searching")
        yield ReasoningDelta("Filtering the inventory to seaside stays near the coast.")
        yield ReasoningDelta("Keeping only TURSAB-licensed hotels to respect local rules.")
        yield StepFinished("Searching")

        for token in tokens(f'Seaside hotels in "{dest}".'):
            yield TextDelta(token)

        if not cart:
            yield StateDelta(
                patch=[
                    {
                        "op": "add",
                        "path": "/cart",
                        "value": {
                            "destination": dest,
                            "hotel": None,
                            "checkIn": None,
                            "checkOut": None,
                            "nights": nights,
                            "currency": "TRY",
                            "total": 0,
                        },
                    }
                ]
            )

        hotels = [
            {
                "id": "htl-lara-bay",
                "name": "Lara Bay Resort",
                "area": "Lara",
                "rating": 4.7,
                "pricePerNight": 5200,
                "currency": "TRY",
                "seaside": True,
                "tursabApproved": True,
                "tags": ["Beachfront", "All-inclusive"],
            },
            {
                "id": "htl-konyaalti-blue",
                "name": "Konyaalti Blue Hotel",
                "area": "Konyaalti",
                "rating": 4.4,
                "pricePerNight": 3800,
                "currency": "TRY",
                "seaside": True,
                "tursabApproved": True,
                "tags": ["Seaview", "Spa"],
            },
            {
                "id": "htl-old-town-house",
                "name": "Kaleici Old Town House",
                "area": "Kaleici",
                "rating": 4.6,
                "pricePerNight": 2900,
                "currency": "TRY",
                "seaside": False,
                "tursabApproved": False,
                "tags": ["Boutique", "Historic"],
            },
        ]

        yield StepStarted("Results")
        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=HOTELS_TOOL,
            args={"title": f"Hotels in {dest}", "hotels": hotels},
        )
        yield StepFinished("Results")

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=DATE_PICKER_TOOL,
            args={
                "title": "Choose your dates",
                "nights": nights,
                "checkIn": "2026-08-14",
                "checkOut": "2026-08-19",
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=TABLE_TOOL,
            args={
                "title": "Regulatory filters",
                "columns": ["Filter", "Applied"],
                "rows": [
                    ["TURSAB licence", "Required"],
                    ["Seaside", "Preferred"],
                    ["Currency", "TRY"],
                ],
            },
        )

        decision: ApprovalDecision = yield ApprovalRequested(
            tool_call_id=call_id(),
            name=APPROVAL_TOOL,
            args={"action": "Confirm the booking", "detail": dest},
        )

        if decision.approved:
            top_hotel = hotels[0]["name"]
            yield StateDelta(
                patch=[{"op": "replace", "path": "/cart/hotel", "value": top_hotel}]
            )
            for token in tokens(f" Booked {top_hotel} in {dest} for {nights} nights."):
                yield TextDelta(token)
        else:
            reason = decision.reason or "no reason given"
            for token in tokens(f" Kept the cart open ({reason}); nothing was booked yet."):
                yield TextDelta(token)

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=SUGGESTED_QUESTIONS_TOOL,
            args={
                "questions": [
                    "Only 5-star hotels",
                    "Cheaper options",
                    "Add airport transfer",
                ],
            },
        )
