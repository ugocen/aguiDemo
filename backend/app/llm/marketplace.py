import json
from collections.abc import AsyncIterator

import httpx

from app.config.settings import Settings
from app.logging.setup import get_logger

log = get_logger("marketplace")


class MarketplaceError(RuntimeError):
    pass


class MarketplaceClient:
    """Streaming client for the GenAI Marketplace gateway.

    The gateway is treated as an OpenAI-compatible chat completions endpoint.
    Configuration is env-driven, nothing here is hardcoded. Two modes are
    supported and the active one is logged at call time:

      stream    consume the gateway token stream and yield deltas as they arrive
      chunked   request a full completion, then yield it progressively so the
                UI still animates when the gateway cannot stream
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._settings.marketplace_api_key}",
            "Content-Type": "application/json",
        }
        if self._settings.marketplace_tenant:
            headers["X-Tenant"] = self._settings.marketplace_tenant
        return headers

    def _payload(self, messages: list[dict], *, stream: bool) -> dict:
        return {
            "model": self._settings.marketplace_model,
            "messages": messages,
            "stream": stream,
        }

    async def stream_completion(self, messages: list[dict]) -> AsyncIterator[str]:
        mode = self._settings.marketplace_stream_mode
        log.info("marketplace_call", mode=mode, model=self._settings.marketplace_model)
        if mode == "stream":
            async for delta in self._stream(messages):
                yield delta
        else:
            async for delta in self._chunked(messages):
                yield delta

    async def _stream(self, messages: list[dict]) -> AsyncIterator[str]:
        url = f"{self._settings.marketplace_base_url}/chat/completions"
        timeout = httpx.Timeout(self._settings.marketplace_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST", url, headers=self._headers(), json=self._payload(messages, stream=True)
            ) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    raise MarketplaceError(f"gateway {response.status_code}: {body.decode(errors='replace')}")
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
                    delta = _extract_delta(event)
                    if delta:
                        yield delta

    async def _chunked(self, messages: list[dict]) -> AsyncIterator[str]:
        url = f"{self._settings.marketplace_base_url}/chat/completions"
        timeout = httpx.Timeout(self._settings.marketplace_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url, headers=self._headers(), json=self._payload(messages, stream=False)
            )
            if response.status_code >= 400:
                raise MarketplaceError(f"gateway {response.status_code}: {response.text}")
            content = _extract_message(response.json())
        for token in _progressive_tokens(content):
            yield token


def _extract_delta(event: dict) -> str:
    try:
        return event["choices"][0]["delta"].get("content") or ""
    except (KeyError, IndexError, TypeError):
        return ""


def _extract_message(payload: dict) -> str:
    try:
        return payload["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return ""


def _progressive_tokens(text: str) -> list[str]:
    words = text.split(" ")
    return [w if i == 0 else " " + w for i, w in enumerate(words)]
