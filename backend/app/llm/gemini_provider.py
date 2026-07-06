import json
from collections.abc import AsyncIterator

import httpx

from app.config.settings import Settings
from app.llm.base import (
    LLMError,
    StreamChunk,
    TextChunk,
    ToolCallChunk,
    split_system,
    tool_call_id,
)
from app.logging.setup import get_logger

log = get_logger("llm")


class GeminiClient:
    """Google Gemini via generateContent (streamGenerateContent, SSE)."""

    provider = "gemini"

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.gemini_base_url.rstrip("/")
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_model
        self._timeout = settings.llm_timeout_seconds

    async def stream_completion(self, messages: list[dict]) -> AsyncIterator[str]:
        async for chunk in self.stream_chat(messages, None):
            if isinstance(chunk, TextChunk) and chunk.text:
                yield chunk.text

    async def stream_chat(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> AsyncIterator[StreamChunk]:
        log.info("llm_call", provider=self.provider, model=self._model, tools=bool(tools))
        system, rest = split_system(messages)
        payload: dict = {"contents": _to_contents(rest)}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        if tools:
            payload["tools"] = [{"functionDeclarations": [_to_declaration(t) for t in tools]}]
            payload["toolConfig"] = {"functionCallingConfig": {"mode": "AUTO"}}
        url = (
            f"{self._base_url}/v1beta/models/{self._model}:streamGenerateContent"
            f"?alt=sse&key={self._api_key}"
        )
        headers = {"content-type": "application/json"}
        async with httpx.AsyncClient(timeout=httpx.Timeout(self._timeout)) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    raise LLMError(f"gemini {response.status_code}: {body.decode(errors='replace')}")
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if not data:
                        continue
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    for chunk in _chunks(event):
                        yield chunk


def _to_declaration(tool: dict) -> dict:
    decl = {"name": tool["name"], "description": tool.get("description", "")}
    params = tool.get("parameters")
    if params and params.get("properties"):
        decl["parameters"] = params
    return decl


def _to_contents(rest: list[dict]) -> list[dict]:
    contents: list[dict] = []
    for m in rest:
        role = m.get("role")
        if role == "tool":
            response = m.get("content")
            if not isinstance(response, dict):
                response = {"result": response}
            contents.append(
                {
                    "role": "user",
                    "parts": [
                        {"functionResponse": {"name": m.get("name", "tool"), "response": response}}
                    ],
                }
            )
        elif role == "assistant":
            parts: list[dict] = []
            if m.get("content"):
                parts.append({"text": m["content"]})
            for tc in m.get("tool_calls", []):
                parts.append({"functionCall": {"name": tc["name"], "args": tc.get("arguments", {})}})
            contents.append({"role": "model", "parts": parts or [{"text": ""}]})
        else:
            contents.append({"role": "user", "parts": [{"text": m.get("content", "")}]})
    return contents


def _chunks(event: dict) -> list[StreamChunk]:
    out: list[StreamChunk] = []
    try:
        parts = event["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError):
        return out
    for p in parts:
        if "functionCall" in p:
            fc = p["functionCall"]
            out.append(
                ToolCallChunk(
                    id=tool_call_id(), name=fc.get("name", ""), arguments=dict(fc.get("args") or {})
                )
            )
        elif p.get("text"):
            out.append(TextChunk(p["text"]))
    return out
