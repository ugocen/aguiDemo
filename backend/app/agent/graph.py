from typing import TypedDict

from ag_ui.core import RunAgentInput
from langgraph.graph import END, START, StateGraph

from app.agent.base import latest_user_text
from app.agent.llm_agent import DEFAULT_SYSTEM, LLMToolAgent
from app.config.settings import Settings


class AgentState(TypedDict, total=False):
    user_text: str
    focus: str


def _plan_node(state: AgentState) -> AgentState:
    text = state.get("user_text", "").lower()
    hints: list[str] = []
    if any(k in text for k in ("table", "compare", "comparison", "matrix")):
        hints.append("a comparison table")
    if any(k in text for k in ("chart", "graph", "trend", "metric", "number")):
        hints.append("a chart")
    if any(k in text for k in ("source", "cite", "citation", "reference")):
        hints.append("citations")
    if any(k in text for k in ("step", "next", "todo", "follow")):
        hints.append("a follow-up list")
    return {"focus": ", ".join(hints)}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("plan", _plan_node)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", END)
    return graph.compile()


class LangGraphAgent(LLMToolAgent):
    """Default real-model agent for the local track.

    A small compiled LangGraph plans a light rendering hint from the user's
    message; the model then decides which frontend tools to call to render cards,
    streaming through the selected LLM provider (Marketplace, OpenAI, Anthropic,
    or Gemini). Tool-calling and the human-in-the-loop loop live in
    ``LLMToolAgent``.
    """

    mode = "langgraph"

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings, system_prompt=DEFAULT_SYSTEM)
        self._graph = build_graph()

    async def _compose_system(self, input: RunAgentInput) -> str:
        plan: AgentState = await self._graph.ainvoke({"user_text": latest_user_text(input)})
        focus = plan.get("focus")
        if focus:
            return f"{self._system} If it fits the request, consider {focus}."
        return self._system
