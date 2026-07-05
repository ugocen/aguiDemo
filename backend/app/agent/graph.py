import uuid
from collections.abc import AsyncIterator
from typing import Any, TypedDict

from ag_ui.core import RunAgentInput
from langgraph.graph import END, START, StateGraph

from app.agent.base import latest_user_text
from app.agent.events import (
    AgentEvent,
    ApprovalRequested,
    DocumentDelta,
    TextDelta,
    ToolCallCompleted,
    ToolCallStarted,
)
from app.agent.tools import lookup_knowledge
from app.agui.catalog import (
    APPROVAL_TOOL,
    FOLLOWUP_TOOL,
    LOOKUP_TOOL,
    SUGGESTED_QUESTIONS_TOOL,
    TABLE_TOOL,
)
from app.agui.resume import ApprovalDecision
from app.config.settings import Settings
from app.llm.marketplace import MarketplaceClient


class AgentState(TypedDict, total=False):
    user_text: str
    wants_lookup: bool
    wants_document: bool
    wants_approval: bool
    wants_table: bool
    wants_followup: bool
    lookup_result: dict[str, Any]
    document_title: str
    document_content: str


def _plan_node(state: AgentState) -> AgentState:
    text = state.get("user_text", "").lower()
    return {
        "wants_lookup": any(k in text for k in ("look up", "lookup", "what is", "explain", "?")),
        "wants_document": any(k in text for k in ("draft", "write", "document", "note", "canvas")),
        "wants_approval": any(k in text for k in ("approve", "deploy", "send", "publish", "confirm")),
        "wants_table": any(k in text for k in ("table", "compare", "comparison", "matrix")),
        "wants_followup": any(k in text for k in ("steps", "next", "follow", "todo")),
    }


def _lookup_node(state: AgentState) -> AgentState:
    if not state.get("wants_lookup"):
        return {}
    return {"lookup_result": lookup_knowledge(state.get("user_text", ""))}


def _document_node(state: AgentState) -> AgentState:
    if not state.get("wants_document"):
        return {}
    result = state.get("lookup_result") or {}
    content = result.get("answer") or "Draft content produced by the agent."
    title = f"Notes on {result.get('matched') or state.get('user_text', 'the request')}"
    return {"document_title": title, "document_content": content}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("plan", _plan_node)
    graph.add_node("lookup", _lookup_node)
    graph.add_node("document", _document_node)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "lookup")
    graph.add_edge("lookup", "document")
    graph.add_edge("document", END)
    return graph.compile()


def _to_chat_messages(input: RunAgentInput) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": "You are a concise assistant in an AG-UI demo workspace. "
            "Answer in two or three sentences.",
        }
    ]
    for message in input.messages or []:
        role = getattr(message, "role", None)
        content = getattr(message, "content", None)
        if role in ("user", "assistant", "system") and isinstance(content, str) and content:
            messages.append({"role": role, "content": content})
    return messages


class LangGraphAgent:
    """LangGraph agent for the local track.

    A small compiled graph plans the run and produces the tool and document
    outputs, while the model node streams real tokens through the Marketplace
    client. The run method exposes semantic agent events that the translator
    maps to AG-UI protocol events, and it receives the approval decision back
    through the generator send channel.
    """

    mode = "langgraph"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._graph = build_graph()
        self._client = MarketplaceClient(settings)

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        user_text = latest_user_text(input)
        plan: AgentState = await self._graph.ainvoke({"user_text": user_text})

        streamed_any = False
        async for delta in self._client.stream_completion(_to_chat_messages(input)):
            streamed_any = True
            yield TextDelta(delta)
        if not streamed_any:
            yield TextDelta("(no content returned by the gateway)")

        if plan.get("wants_lookup") and plan.get("lookup_result"):
            tool_call_id = f"call_{uuid.uuid4().hex[:8]}"
            yield ToolCallStarted(
                tool_call_id=tool_call_id, name=LOOKUP_TOOL, args={"query": user_text}
            )
            yield ToolCallCompleted(tool_call_id=tool_call_id, result=plan["lookup_result"])

        if plan.get("wants_document"):
            yield DocumentDelta(
                patch=[{"op": "replace", "path": "/document/title", "value": plan["document_title"]}]
            )
            yield DocumentDelta(
                patch=[
                    {
                        "op": "replace",
                        "path": "/document/content",
                        "value": plan["document_content"],
                    }
                ]
            )

        if plan.get("wants_table"):
            yield ToolCallStarted(
                tool_call_id=f"call_{uuid.uuid4().hex[:8]}",
                name=TABLE_TOOL,
                args={
                    "title": "AG-UI event categories",
                    "columns": ["Category", "Example event", "Rendered as"],
                    "rows": [
                        ["Lifecycle", "RUN_STARTED", "run state"],
                        ["Text", "TEXT_MESSAGE_CONTENT", "chat bubble"],
                        ["Tool", "TOOL_CALL_START", "tool card"],
                        ["State", "STATE_DELTA", "canvas edit"],
                    ],
                },
            )

        if plan.get("wants_followup"):
            yield ToolCallStarted(
                tool_call_id=f"call_{uuid.uuid4().hex[:8]}",
                name=FOLLOWUP_TOOL,
                args={
                    "title": "Next steps",
                    "items": [
                        {"label": "Review the draft", "detail": "Open the canvas panel."},
                        {"label": "Ask a follow-up", "detail": "Use a suggested question."},
                    ],
                },
            )

        yield ToolCallStarted(
            tool_call_id=f"call_{uuid.uuid4().hex[:8]}",
            name=SUGGESTED_QUESTIONS_TOOL,
            args={"questions": ["What is SSE?", "Explain AgentCore", "Compare the event types"]},
        )

        if plan.get("wants_approval"):
            approval_id = f"call_{uuid.uuid4().hex[:8]}"
            decision: ApprovalDecision = yield ApprovalRequested(
                tool_call_id=approval_id,
                name=APPROVAL_TOOL,
                args={"action": "Proceed with the request", "detail": user_text},
            )
            if decision.approved:
                yield TextDelta(" Approved, proceeding.")
            else:
                yield TextDelta(
                    f" Rejected ({decision.reason or 'no reason given'}), stopping here."
                )
