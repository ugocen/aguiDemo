import json
from collections.abc import AsyncIterator

import httpx

from app.llm.base import (
    LLMError,
    StreamChunk,
    TextChunk,
    ToolCallChunk,
    progressive_tokens,
    tool_call_id,
)
from app.logging.setup import get_logger

log = get_logger("llm")


class OpenAICompatibleClient:
    """Streaming client for any OpenAI-compatible chat completions endpoint.

    Used for both the GenAI Marketplace gateway and OpenAI itself. Two modes are
    supported and the active one is logged at call time:

      stream    consume the token stream and yield deltas as they arrive
      chunked   request a full completion, then yield it progressively so the UI
                still animates when the endpoint cannot stream

    ``stream_chat`` adds tool-calling: the model may return function calls, which
    are streamed as ``ToolCallChunk`` alongside text.
    """

    provider = "openai-compatible"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        stream_mode: str = "stream",
        timeout_seconds: float = 60.0,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._stream_mode = stream_mode
        self._timeout = timeout_seconds
        self._extra_headers = extra_headers or {}

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            **self._extra_headers,
        }

    def _payload(self, messages: list[dict], *, stream: bool) -> dict:
        return {"model": self._model, "messages": messages, "stream": stream}

    async def stream_completion(self, messages: list[dict]) -> AsyncIterator[str]:
        log.info("llm_call", provider=self.provider, mode=self._stream_mode, model=self._model)
        if self._stream_mode == "chunked":
            async for delta in self._chunked(messages):
                yield delta
        else:
            async for delta in self._stream(messages):
                yield delta

    async def _stream(self, messages: list[dict]) -> AsyncIterator[str]:
        url = f"{self._base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=httpx.Timeout(self._timeout)) as client:
            async with client.stream(
                "POST", url, headers=self._headers(), json=self._payload(messages, stream=True)
            ) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    raise LLMError(f"{self.provider} {response.status_code}: {body.decode(errors='replace')}")
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    try:
                        delta = event["choices"][0]["delta"].get("content") or ""
                    except (KeyError, IndexError, TypeError):
                        delta = ""
                    if delta:
                        yield delta

    async def _chunked(self, messages: list[dict]) -> AsyncIterator[str]:
        url = f"{self._base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=httpx.Timeout(self._timeout)) as client:
            response = await client.post(
                url, headers=self._headers(), json=self._payload(messages, stream=False)
            )
            if response.status_code >= 400:
                raise LLMError(f"{self.provider} {response.status_code}: {response.text}")
            try:
                content = response.json()["choices"][0]["message"]["content"] or ""
            except (KeyError, IndexError, TypeError):
                content = ""
        for token in progressive_tokens(content):
            yield token

    async def stream_chat(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> AsyncIterator[StreamChunk]:
        log.info(
            "llm_call", provider=self.provider, mode="stream", model=self._model, tools=bool(tools)
        )
        wire = [_to_openai_message(m) for m in messages]
        payload: dict = {"model": self._model, "messages": wire, "stream": True}
        if tools:
            payload["tools"] = [{"type": "function", "function": _to_function(t)} for t in tools]
            payload["tool_choice"] = "auto"
        url = f"{self._base_url}/chat/completions"
        calls: dict[int, dict] = {}
        async with httpx.AsyncClient(timeout=httpx.Timeout(self._timeout)) as client:
            async with client.stream(
                "POST", url, headers=self._headers(), json=payload
            ) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    raise LLMError(f"{self.provider} {response.status_code}: {body.decode(errors='replace')}")
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    try:
                        delta = event["choices"][0]["delta"]
                    except (KeyError, IndexError, TypeError):
                        continue
                    if delta.get("content"):
                        yield TextChunk(delta["content"])
                    for tc in delta.get("tool_calls") or []:
                        idx = tc.get("index", 0)
                        slot = calls.setdefault(idx, {"id": None, "name": "", "args": ""})
                        if tc.get("id"):
                            slot["id"] = tc["id"]
                        fn = tc.get("function") or {}
                        if fn.get("name"):
                            slot["name"] = fn["name"]
                        if fn.get("arguments"):
                            slot["args"] += fn["arguments"]
        for idx in sorted(calls):
            slot = calls[idx]
            if not slot["name"]:
                continue
            try:
                args = json.loads(slot["args"] or "{}")
            except json.JSONDecodeError:
                args = {}
            yield ToolCallChunk(
                id=slot["id"] or tool_call_id(),
                name=slot["name"],
                arguments=args if isinstance(args, dict) else {},
            )


def _to_function(tool: dict) -> dict:
    return {
        "name": tool["name"],
        "description": tool.get("description", ""),
        "parameters": tool.get("parameters") or {"type": "object", "properties": {}},
    }


def _to_openai_message(m: dict) -> dict:
    role = m.get("role")
    if role == "tool":
        content = m.get("content")
        if not isinstance(content, str):
            content = json.dumps(content)
        return {"role": "tool", "tool_call_id": m.get("tool_call_id", ""), "content": content}
    if role == "assistant" and m.get("tool_calls"):
        return {
            "role": "assistant",
            "content": m.get("content") or None,
            "tool_calls": [
                {
                    "id": tc.get("id"),
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": json.dumps(tc.get("arguments", {}))},
                }
                for tc in m["tool_calls"]
            ],
        }
    return {"role": role, "content": m.get("content", "")}
