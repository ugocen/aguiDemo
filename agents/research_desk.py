from collections.abc import AsyncIterator

from ag_ui.core import RunAgentInput

from app.agent.base import latest_user_text
from app.agent.events import (
    AgentEvent,
    ReasoningDelta,
    StepFinished,
    StepStarted,
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


class ResearchDeskAgent:
    """Reasons over sources and compares them with citations.

    Showcases agentic_chat_reasoning plus backend tool rendering.
    """

    id = "research-desk"
    name = "Research Desk"
    description = "Reasons over sources and compares them with citations"
    mode = "scenario"

    system_prompt = (
        "You are a research assistant that thinks briefly out loud about how "
        "you will approach the question, looks it up with lookupKnowledge, "
        "compares how sources line up in a renderTable, backs claims with "
        "renderCitations, and offers renderSuggestedQuestions to go deeper. "
        "Keep prose to one or two sentences."
    )
    allowed_tools = [
        LOOKUP_TOOL,
        TABLE_TOOL,
        CITATIONS_TOOL,
        SUGGESTED_QUESTIONS_TOOL,
    ]

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        q = latest_user_text(input) or "AG-UI"

        yield StepStarted("Thinking")
        yield ReasoningDelta("Let me figure out which sources actually speak to this.")
        yield ReasoningDelta("The primary docs are authoritative, so I weigh them highest.")
        yield ReasoningDelta("The knowledge base adds context, but I treat it as secondary.")
        yield ReasoningDelta("I'll line them up side by side and see where they agree.")
        yield StepFinished("Thinking")

        for token in tokens(f'Researching "{q}".'):
            yield TextDelta(token)

        lid = call_id()
        yield ToolCallStarted(tool_call_id=lid, name=LOOKUP_TOOL, args={"query": q})
        result = lookup_knowledge(q)
        yield ToolCallCompleted(tool_call_id=lid, result=result)

        answer = result.get("answer") or ""
        snippet = answer[:120]

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=TABLE_TOOL,
            args={
                "title": f'Sources on "{q}"',
                "columns": ["Source", "Confidence", "Summary"],
                "rows": [
                    ["Primary docs", "High", snippet],
                    ["Knowledge base", "Medium", "Corroborates the core claim."],
                    ["Community notes", "Low", "Anecdotal, useful for edge cases."],
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=CITATIONS_TOOL,
            args={
                "title": "Backing sources",
                "sources": [
                    {
                        "title": "AG-UI documentation",
                        "url": "https://docs.ag-ui.com",
                        "snippet": "Official protocol reference for AG-UI events.",
                    },
                    {
                        "title": "Knowledge base",
                        "url": "kb://knowledge",
                        "snippet": result.get("matched") or snippet,
                    },
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=SUGGESTED_QUESTIONS_TOOL,
            args={
                "questions": [
                    f"How reliable is the evidence on {q}?",
                    "Where do the sources disagree?",
                    "What should I read next?",
                ],
            },
        )

        for token in tokens("Want me to dig into any of these threads further?"):
            yield TextDelta(token)
