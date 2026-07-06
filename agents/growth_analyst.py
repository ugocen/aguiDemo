from collections.abc import AsyncIterator

from ag_ui.core import RunAgentInput

from app.agent.base import latest_user_text
from app.agent.events import (
    AgentEvent,
    ReasoningDelta,
    StepFinished,
    StepStarted,
    TextDelta,
    ToolCallStarted,
)
from app.agui.catalog import CHART_TOOL, FOLLOWUP_TOOL, SUGGESTED_QUESTIONS_TOOL, TABLE_TOOL

from agents._common import call_id, tokens


class GrowthAnalystAgent:
    """Growth scenario, turns metrics into a table, a chart and insights.

    Showcases tool_based_generative_ui: structured data rendered as cards.
    """

    id = "growth-analyst"
    name = "Growth Analyst"
    description = "Turns metrics into tables, charts and insights"
    mode = "scenario"

    system_prompt = (
        "You are a growth analyst. Briefly reason about the metric that matters, "
        "present the numbers as a renderTable and the same figures as a "
        "renderChart, call out what stands out with renderFollowUp, and offer "
        "renderSuggestedQuestions. If the user gives no figures, invent small, "
        "plausible demo numbers. Keep prose to one or two sentences."
    )
    allowed_tools = [TABLE_TOOL, CHART_TOOL, FOLLOWUP_TOOL, SUGGESTED_QUESTIONS_TOOL]

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        subject = latest_user_text(input) or "the funnel"

        yield StepStarted("Thinking")
        yield ReasoningDelta("Conversion is the metric that gates every stage below it.")
        yield ReasoningDelta("Leading with the funnel makes the biggest drop-off obvious.")
        yield StepFinished("Thinking")

        for token in tokens(f'Analyzing "{subject}". Here is the funnel.'):
            yield TextDelta(token)

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=TABLE_TOOL,
            args={
                "title": "Signup funnel",
                "columns": ["Stage", "Users", "Conversion"],
                "rows": [
                    ["Visited", "4200", "100%"],
                    ["Signed up", "1680", "40%"],
                    ["Activated", "840", "50%"],
                    ["Retained", "336", "40%"],
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=CHART_TOOL,
            args={
                "title": "Users by stage",
                "unit": "",
                "series": [
                    {"label": "Visited", "value": 4200},
                    {"label": "Signed up", "value": 1680},
                    {"label": "Activated", "value": 840},
                    {"label": "Retained", "value": 336},
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=FOLLOWUP_TOOL,
            args={
                "title": "What stands out",
                "items": [
                    {
                        "label": "Signup is the leak",
                        "detail": "Sixty percent drop from visit to signup dwarfs later stages.",
                    },
                    {
                        "label": "Activation holds",
                        "detail": "Half of new signups activate, a healthy mid-funnel.",
                    },
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=SUGGESTED_QUESTIONS_TOOL,
            args={
                "questions": [
                    "Why do visitors not sign up?",
                    "Compare this to last month",
                    "Segment by channel",
                ],
            },
        )

        for token in tokens(" Want me to break any stage down further?"):
            yield TextDelta(token)
