import json
from collections.abc import AsyncIterator

import httpx

from app.config.settings import Settings
from app.llm.base import LLMError, split_system
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
        log.info("llm_call", provider=self.provider, model=self._model)
        system, rest = split_system(messages)
        payload: dict = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": [{"role": m["role"], "content": m.get("content", "")} for m in rest],
            "stream": True,
        }
        if system:
            payload["system"] = system
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": self._version,
            "content-type": "application/json",
        }
        url = f"{self._base_url}/v1/messages"
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
                    if event.get("type") == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta" and delta.get("text"):
                            yield delta["text"]
