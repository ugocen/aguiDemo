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
from app.agui.catalog import APPROVAL_TOOL, LOOKUP_TOOL, tool_catalog
from app.agui.resume import ApprovalDecision
from app.config.settings import Settings
from app.llm.base import LLMError, TextChunk, ToolCallChunk
from app.llm.factory import build_llm

DEFAULT_SYSTEM = (
    "You are a helpful assistant in an AG-UI demo workspace. Keep prose short, "
    "one to three sentences. You render rich UI by calling the provided tools "
    "instead of describing data in text: call renderTable for tabular data, "
    "renderChart for numeric series, renderFollowUp for next steps, "
    "renderCitations for sources, renderSuggestedQuestions for follow-up prompts, "
    "and lookupKnowledge to look a fact up. Only call a tool when it genuinely "
    "helps; a plain answer is fine otherwise."
)

# Encourage the model to emit all needed tool calls in a single turn. Each turn
# is one provider request, so batching keeps runs fast and gentle on rate limits.
TOOL_BATCH_HINT = "If several cards apply, call all the needed tools together in one turn."


def _friendly_error(exc: LLMError) -> str:
    message = str(exc)
    if " 429" in message or "RESOURCE_EXHAUSTED" in message.upper():
        return (
            " [The model provider is rate limited right now (free-tier quota); "
            "please retry in a minute.]"
        )
    return " [The model call failed; please try again.]"


class LLMToolAgent:
    """Agent that lets the model decide which frontend card to render.

    It runs a bounded tool-use loop over the vendor-agnostic ``stream_chat``:
    text is streamed as ``TextDelta``; a render-only tool call becomes a
    ``ToolCallStarted`` (the frontend renders the card); ``lookupKnowledge`` runs
    the backend tool and yields ``ToolCallStarted``/``ToolCallCompleted``;
    ``requestApproval`` suspends via ``ApprovalRequested`` and resumes on the
    decision. Tool results are fed back so the model can continue. Only the
    translator emits protocol events, so this agent stays pure.
    """

    mode = "langgraph"

    def __init__(
        self,
        settings: Settings,
        *,
        system_prompt: str = DEFAULT_SYSTEM,
        allowed_tools: list[str] | None = None,
        max_turns: int = 4,
    ) -> None:
        self._settings = settings
        self._client = build_llm(settings)
        self._system = system_prompt
        self._allowed = set(allowed_tools) if allowed_tools is not None else None
        self._max_turns = max_turns

    async def _compose_system(self, input: RunAgentInput) -> str:
        return self._system

    def _tools(self, input: RunAgentInput) -> list[dict]:
        catalog = tool_catalog()
        client_names = {
            getattr(t, "name", None) if not isinstance(t, dict) else t.get("name")
            for t in (input.tools or [])
        }
        client_names.discard(None)
        tools = catalog
        if client_names:
            tools = [t for t in tools if t["name"] in client_names]
        if self._allowed is not None:
            tools = [t for t in tools if t["name"] in self._allowed]
        return tools

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        system = f"{await self._compose_system(input)} {TOOL_BATCH_HINT}"
        messages: list[dict] = [{"role": "system", "content": system}]
        for m in input.messages or []:
            role = getattr(m, "role", None)
            content = getattr(m, "content", None)
            if role in ("user", "assistant") and isinstance(content, str) and content:
                messages.append({"role": role, "content": content})
        if not any(m["role"] == "user" for m in messages):
            messages.append({"role": "user", "content": latest_user_text(input) or "Hello"})

        tools = self._tools(input)
        tools_enabled = tools

        for _turn in range(self._max_turns):
            calls: list[ToolCallChunk] = []
            assistant_text = ""
            streamed_any = False
            try:
                async for chunk in self._client.stream_chat(messages, tools_enabled):
                    streamed_any = True
                    if isinstance(chunk, TextChunk):
                        if chunk.text:
                            assistant_text += chunk.text
                            yield TextDelta(chunk.text)
                    elif isinstance(chunk, ToolCallChunk):
                        calls.append(chunk)
            except LLMError as exc:
                yield TextDelta(_friendly_error(exc))
                return

            if not calls:
                if not streamed_any and _turn == 0:
                    yield TextDelta("(no content returned by the model)")
                return

            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_text,
                    "tool_calls": [
                        {"id": c.id, "name": c.name, "arguments": c.arguments} for c in calls
                    ],
                }
            )

            for c in calls:
                if c.name == LOOKUP_TOOL:
                    yield ToolCallStarted(tool_call_id=c.id, name=c.name, args=c.arguments)
                    result = lookup_knowledge(str(c.arguments.get("query", "")))
                    yield ToolCallCompleted(tool_call_id=c.id, result=result)
                    messages.append(
                        {"role": "tool", "tool_call_id": c.id, "name": c.name, "content": result}
                    )
                elif c.name == APPROVAL_TOOL:
                    decision: ApprovalDecision = yield ApprovalRequested(
                        tool_call_id=c.id, name=c.name, args=c.arguments
                    )
                    result = (
                        decision.to_result()
                        if decision is not None
                        else {"approved": False, "reason": "no decision"}
                    )
                    messages.append(
                        {"role": "tool", "tool_call_id": c.id, "name": c.name, "content": result}
                    )
                else:
                    yield ToolCallStarted(tool_call_id=c.id, name=c.name, args=c.arguments)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": c.id,
                            "name": c.name,
                            "content": {"status": "rendered"},
                        }
                    )

            # A render-only turn has nothing more for the model to react to; stop
            # offering tools so the follow-up turn is a text wrap-up, not a repeat
            # of the same cards. Backend/HITL calls keep tools on for a real reply.
            if not any(c.name in (LOOKUP_TOOL, APPROVAL_TOOL) for c in calls):
                tools_enabled = None
