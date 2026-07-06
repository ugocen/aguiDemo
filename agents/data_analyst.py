from collections.abc import AsyncIterator

from ag_ui.core import RunAgentInput

from app.agent.base import latest_user_text
from app.agent.events import AgentEvent, TextDelta, ToolCallStarted
from app.agui.catalog import CHART_TOOL, FOLLOWUP_TOOL, SUGGESTED_QUESTIONS_TOOL, TABLE_TOOL

from agents._common import call_id, tokens


class DataAnalystAgent:
    """Analytics scenario, presents a metrics table and derived next steps.

    Card types exercised: streaming text, a data table, a follow-up insights
    list, and suggested questions. No human-in-the-loop.
    """

    id = "data-analyst"
    name = "Data Analyst"
    description = "Presents a metrics table and derived insights"
    mode = "scenario"

    system_prompt = (
        "You are a data analyst. Present metrics as a renderTable and a "
        "renderChart of the same numbers, summarize what stands out with "
        "renderFollowUp, and offer renderSuggestedQuestions. If the user gives no "
        "figures, invent small, plausible demo numbers. Keep prose to one or two "
        "sentences."
    )
    allowed_tools = [TABLE_TOOL, CHART_TOOL, FOLLOWUP_TOOL, SUGGESTED_QUESTIONS_TOOL]

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        subject = latest_user_text(input) or "the run"

        for token in tokens(f'Analyzing "{subject}". Here are the numbers.'):
            yield TextDelta(token)

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=TABLE_TOOL,
            args={
                "title": "Event counts by category",
                "columns": ["Category", "Events", "Share"],
                "rows": [
                    ["Text", "22", "58%"],
                    ["Tool", "8", "21%"],
                    ["State", "5", "13%"],
                    ["Lifecycle", "3", "8%"],
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=CHART_TOOL,
            args={
                "title": "Events by category",
                "unit": "",
                "series": [
                    {"label": "Text", "value": 22},
                    {"label": "Tool", "value": 8},
                    {"label": "State", "value": 5},
                    {"label": "Lifecycle", "value": 3},
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=FOLLOWUP_TOOL,
            args={
                "title": "Insights",
                "items": [
                    {"label": "Text dominates", "detail": "Most events are streamed tokens."},
                    {"label": "Tools are visible", "detail": "One in five events is a tool call."},
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=SUGGESTED_QUESTIONS_TOOL,
            args={"questions": ["Break down by run", "Show the slowest step", "Export as a table"]},
        )

        for token in tokens(" Want me to break any row down further?"):
            yield TextDelta(token)
