from collections.abc import AsyncIterator

from ag_ui.core import RunAgentInput

from app.agent.base import latest_user_text
from app.agent.events import (
    AgentEvent,
    TextDelta,
    ToolCallCompleted,
    ToolCallStarted,
)
from app.agent.tools import lookup_knowledge
from app.agui.catalog import (
    CITATIONS_TOOL,
    LOOKUP_TOOL,
    SUGGESTED_QUESTIONS_TOOL,
    TABLE_TOOL,
)

from agents._common import call_id, tokens


class ResearchAssistantAgent:
    """Research scenario, looks a topic up and compares sources in a table.

    Card types exercised: streaming text, lookup tool card, table, suggested
    questions. No human-in-the-loop, research is read-only.
    """

    id = "research-assistant"
    name = "Research Assistant"
    description = "Looks a topic up and compares sources in a table"
    mode = "scenario"

    system_prompt = (
        "You are a research assistant. Look the user's topic up with "
        "lookupKnowledge, compare how a few sources line up in a renderTable, "
        "back it with renderCitations, and offer renderSuggestedQuestions for "
        "going deeper. Keep prose to one or two sentences."
    )
    allowed_tools = [LOOKUP_TOOL, TABLE_TOOL, CITATIONS_TOOL, SUGGESTED_QUESTIONS_TOOL]

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        query = latest_user_text(input) or "AG-UI"

        for token in tokens(f'Researching "{query}".'):
            yield TextDelta(token)

        lookup = call_id()
        yield ToolCallStarted(tool_call_id=lookup, name=LOOKUP_TOOL, args={"query": query})
        result = lookup_knowledge(query)
        yield ToolCallCompleted(tool_call_id=lookup, result=result)

        for token in tokens(" Here is how a few sources line up."):
            yield TextDelta(token)

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=TABLE_TOOL,
            args={
                "title": f"Sources on {result.get('matched') or query}",
                "columns": ["Source", "Confidence", "Summary"],
                "rows": [
                    ["Knowledge base", "high", result["answer"][:60] + "..."],
                    ["Protocol spec", "medium", "Typed events over SSE"],
                    ["Community docs", "medium", "Examples and integrations"],
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=CITATIONS_TOOL,
            args={
                "title": "Sources",
                "sources": [
                    {
                        "title": "AG-UI protocol",
                        "url": "https://docs.ag-ui.com",
                        "snippet": "Typed events streamed over SSE.",
                    },
                    {
                        "title": "Demo knowledge base",
                        "url": "",
                        "snippet": result["answer"][:60] + "...",
                    },
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=SUGGESTED_QUESTIONS_TOOL,
            args={"questions": ["Compare with SSE", "Explain AgentCore", "Show related tools"]},
        )

        for token in tokens(" Ask a follow-up to go deeper."):
            yield TextDelta(token)
