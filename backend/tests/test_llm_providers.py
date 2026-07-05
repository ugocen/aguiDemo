import pytest

from app.config.settings import Settings
from app.llm import anthropic_provider, gemini_provider, openai_compatible
from app.llm.factory import build_llm


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


async def _collect(client, messages):
    return "".join([delta async for delta in client.stream_completion(messages)])


@pytest.mark.asyncio
async def test_openai_compatible_parsing(monkeypatch):
    lines = [
        'data: {"choices":[{"delta":{"content":"Hel"}}]}',
        'data: {"choices":[{"delta":{"content":"lo"}}]}',
        "data: [DONE]",
    ]
    _patch(monkeypatch, openai_compatible, lines)
    client = openai_compatible.OpenAICompatibleClient(base_url="http://x", api_key="k", model="m")
    assert await _collect(client, [{"role": "user", "content": "hi"}]) == "Hello"


@pytest.mark.asyncio
async def test_anthropic_parsing_and_system_split(monkeypatch):
    lines = [
        "event: content_block_delta",
        'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hi "}}',
        'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"there"}}',
        'data: {"type":"message_stop"}',
    ]
    _patch(monkeypatch, anthropic_provider, lines)
    client = anthropic_provider.AnthropicClient(Settings(anthropic_api_key="k"))
    out = await _collect(client, [{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}])
    assert out == "Hi there"


@pytest.mark.asyncio
async def test_gemini_parsing(monkeypatch):
    lines = [
        'data: {"candidates":[{"content":{"parts":[{"text":"Ge"}]}}]}',
        'data: {"candidates":[{"content":{"parts":[{"text":"mini"}]}}]}',
    ]
    _patch(monkeypatch, gemini_provider, lines)
    client = gemini_provider.GeminiClient(Settings(gemini_api_key="k"))
    assert await _collect(client, [{"role": "user", "content": "hi"}]) == "Gemini"


def test_factory_selects_each_provider():
    names = {
        "marketplace": "MarketplaceClient",
        "openai": "OpenAIClient",
        "anthropic": "AnthropicClient",
        "gemini": "GeminiClient",
    }
    for provider, cls in names.items():
        assert type(build_llm(Settings(llm_provider=provider))).__name__ == cls
