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


class AnthropicClient:
    """Anthropic (Claude) via the Messages API with SSE streaming."""

    provider = "anthropic"

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.anthropic_base_url.rstrip("/")
        self._api_key = settings.anthropic_api_key
        self._model = settings.anthropic_model
        self._version = settings.anthropic_version
        self._max_tokens = settings.anthropic_max_tokens
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
        payload: dict = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": _to_messages(rest),
            "stream": True,
        }
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = [_to_tool(t) for t in tools]
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": self._version,
            "content-type": "application/json",
        }
        url = f"{self._base_url}/v1/messages"
        blocks: dict[int, dict] = {}
        async with httpx.AsyncClient(timeout=httpx.Timeout(self._timeout)) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    raise LLMError(f"anthropic {response.status_code}: {body.decode(errors='replace')}")
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    etype = event.get("type")
                    if etype == "content_block_start":
                        block = event.get("content_block", {})
                        if block.get("type") == "tool_use":
                            blocks[event.get("index")] = {
                                "id": block.get("id"),
                                "name": block.get("name", ""),
                                "args": "",
                            }
                    elif etype == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta" and delta.get("text"):
                            yield TextChunk(delta["text"])
                        elif delta.get("type") == "input_json_delta":
                            slot = blocks.get(event.get("index"))
                            if slot is not None:
                                slot["args"] += delta.get("partial_json", "")
                    elif etype == "content_block_stop":
                        slot = blocks.pop(event.get("index"), None)
                        if slot is not None and slot["name"]:
                            try:
                                args = json.loads(slot["args"] or "{}")
                            except json.JSONDecodeError:
                                args = {}
                            yield ToolCallChunk(
                                id=slot["id"] or tool_call_id(),
                                name=slot["name"],
                                arguments=args if isinstance(args, dict) else {},
                            )


def _to_tool(tool: dict) -> dict:
    return {
        "name": tool["name"],
        "description": tool.get("description", ""),
        "input_schema": tool.get("parameters") or {"type": "object", "properties": {}},
    }


def _to_messages(rest: list[dict]) -> list[dict]:
    out: list[dict] = []
    for m in rest:
        role = m.get("role")
        if role == "tool":
            content = m.get("content")
            if not isinstance(content, str):
                content = json.dumps(content)
            block = {"type": "tool_result", "tool_use_id": m.get("tool_call_id", ""), "content": content}
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
        elif role == "assistant" and m.get("tool_calls"):
            content: list[dict] = []
            if m.get("content"):
                content.append({"type": "text", "text": m["content"]})
            for tc in m["tool_calls"]:
                content.append(
                    {"type": "tool_use", "id": tc.get("id"), "name": tc["name"], "input": tc.get("arguments", {})}
                )
            out.append({"role": "assistant", "content": content})
        else:
            out.append({"role": role, "content": m.get("content", "")})
    return out
