import json
from types import SimpleNamespace

import pytest

from app.agent import llm_agent
from app.agent.events import ApprovalRequested, TextDelta, ToolCallCompleted, ToolCallStarted
from app.agui.catalog import APPROVAL_TOOL, CHART_TOOL, LOOKUP_TOOL, TABLE_TOOL
from app.agui.resume import ApprovalDecision
from app.config.settings import Settings
from app.llm import anthropic_provider, gemini_provider, openai_compatible
from app.llm.base import TextChunk, ToolCallChunk


# --- provider stream_chat parsing (mock SSE) --------------------------------


class FakeResponse:
    def __init__(self, lines, status=200):
        self._lines = lines
        self.status_code = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def aiter_lines(self):
        for line in self._lines:
            yield line

    async def aread(self):
        return b"error"


class FakeClient:
    def __init__(self, resp):
        self._resp = resp

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def stream(self, *args, **kwargs):
        return self._resp


def _patch(monkeypatch, module, lines):
    resp = FakeResponse(lines)
    monkeypatch.setattr(module.httpx, "AsyncClient", lambda *a, **k: FakeClient(resp))


async def _chat(client, tools):
    return [c async for c in client.stream_chat([{"role": "user", "content": "hi"}], tools)]


def _sse(obj) -> str:
    return "data: " + json.dumps(obj)


CHART_TOOL_DEF = [
    {"name": CHART_TOOL, "description": "chart", "parameters": {"type": "object", "properties": {}}}
]


@pytest.mark.asyncio
async def test_openai_tool_call_parsing(monkeypatch):
    lines = [
        _sse({"choices": [{"delta": {"tool_calls": [
            {"index": 0, "id": "call_1", "function": {"name": CHART_TOOL, "arguments": '{"title":'}}
        ]}}]}),
        _sse({"choices": [{"delta": {"tool_calls": [
            {"index": 0, "function": {"arguments": '"X"}'}}
        ]}}]}),
        "data: [DONE]",
    ]
    _patch(monkeypatch, openai_compatible, lines)
    client = openai_compatible.OpenAICompatibleClient(base_url="http://x", api_key="k", model="m")
    calls = [c for c in await _chat(client, CHART_TOOL_DEF) if isinstance(c, ToolCallChunk)]
    assert len(calls) == 1
    assert calls[0].name == CHART_TOOL and calls[0].arguments == {"title": "X"}


@pytest.mark.asyncio
async def test_gemini_tool_call_parsing(monkeypatch):
    lines = [
        _sse({"candidates": [{"content": {"parts": [
            {"functionCall": {"name": CHART_TOOL, "args": {"title": "X"}}}
        ]}}]})
    ]
    _patch(monkeypatch, gemini_provider, lines)
    client = gemini_provider.GeminiClient(Settings(gemini_api_key="k"))
    calls = [c for c in await _chat(client, CHART_TOOL_DEF) if isinstance(c, ToolCallChunk)]
    assert len(calls) == 1
    assert calls[0].name == CHART_TOOL and calls[0].arguments == {"title": "X"}


@pytest.mark.asyncio
async def test_anthropic_tool_call_parsing(monkeypatch):
    lines = [
        _sse({"type": "content_block_start", "index": 0,
              "content_block": {"type": "tool_use", "id": "tu_1", "name": CHART_TOOL}}),
        _sse({"type": "content_block_delta", "index": 0,
              "delta": {"type": "input_json_delta", "partial_json": '{"title":'}}),
        _sse({"type": "content_block_delta", "index": 0,
              "delta": {"type": "input_json_delta", "partial_json": '"X"}'}}),
        _sse({"type": "content_block_stop", "index": 0}),
    ]
    _patch(monkeypatch, anthropic_provider, lines)
    client = anthropic_provider.AnthropicClient(Settings(anthropic_api_key="k"))
    calls = [c for c in await _chat(client, CHART_TOOL_DEF) if isinstance(c, ToolCallChunk)]
    assert len(calls) == 1
    assert calls[0].name == CHART_TOOL and calls[0].arguments == {"title": "X"}


# --- LLMToolAgent loop (fake LLM) -------------------------------------------


class FakeLLM:
    def __init__(self, turns):
        self._turns = turns
        self._i = 0

    async def stream_chat(self, messages, tools=None):
        turn = self._turns[min(self._i, len(self._turns) - 1)]
        self._i += 1
        for chunk in turn:
            yield chunk


def _make_input(text="hi", tools=None):
    return SimpleNamespace(
        messages=[SimpleNamespace(role="user", content=text)], tools=tools or []
    )


def _agent(monkeypatch, turns, **kwargs):
    monkeypatch.setattr(llm_agent, "build_llm", lambda settings: FakeLLM(turns))
    return llm_agent.LLMToolAgent(Settings(), **kwargs)


async def _drive(agent, input, decisions=None):
    decisions = list(decisions or [])
    events = []
    gen = agent.run(input)
    to_send = None
    while True:
        try:
            event = await gen.asend(to_send)
        except StopAsyncIteration:
            break
        events.append(event)
        to_send = None
        if isinstance(event, ApprovalRequested):
            to_send = decisions.pop(0) if decisions else ApprovalDecision(approved=True)
    return events


@pytest.mark.asyncio
async def test_agent_renders_model_chosen_card(monkeypatch):
    turns = [
        [TextChunk("Here."), ToolCallChunk(id="c1", name=TABLE_TOOL, arguments={"columns": ["A"], "rows": [["1"]]})],
        [TextChunk(" Done.")],
    ]
    events = await _drive(_agent(monkeypatch, turns), _make_input())
    starts = [e for e in events if isinstance(e, ToolCallStarted)]
    assert [e.name for e in starts] == [TABLE_TOOL]
    assert any(isinstance(e, TextDelta) for e in events)


@pytest.mark.asyncio
async def test_agent_runs_lookup_backend_tool(monkeypatch):
    turns = [
        [ToolCallChunk(id="c1", name=LOOKUP_TOOL, arguments={"query": "ag-ui"})],
        [TextChunk("AG-UI is a protocol.")],
    ]
    events = await _drive(_agent(monkeypatch, turns), _make_input())
    completed = [e for e in events if isinstance(e, ToolCallCompleted)]
    assert completed and completed[0].result["matched"] == "ag-ui"


@pytest.mark.asyncio
async def test_agent_suspends_for_approval(monkeypatch):
    turns = [
        [ToolCallChunk(id="c1", name=APPROVAL_TOOL, arguments={"action": "Escalate"})],
        [TextChunk("Escalated.")],
    ]
    events = await _drive(
        _agent(monkeypatch, turns),
        _make_input(),
        decisions=[ApprovalDecision(approved=True, reason="ok")],
    )
    assert any(isinstance(e, ApprovalRequested) for e in events)
    assert any(isinstance(e, TextDelta) and "Escalated" in e.text for e in events)


@pytest.mark.asyncio
async def test_allowed_tools_restrict_catalog(monkeypatch):
    agent = _agent(monkeypatch, [[TextChunk("hi")]], allowed_tools=[CHART_TOOL])
    tools = agent._tools(_make_input())
    assert [t["name"] for t in tools] == [CHART_TOOL]
