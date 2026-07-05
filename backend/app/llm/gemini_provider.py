import json
from collections.abc import AsyncIterator

import httpx

from app.config.settings import Settings
from app.llm.base import LLMError, split_system
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
        log.info("llm_call", provider=self.provider, model=self._model)
        system, rest = split_system(messages)
        contents = [
            {
                "role": "model" if m.get("role") == "assistant" else "user",
                "parts": [{"text": m.get("content", "")}],
            }
            for m in rest
        ]
        payload: dict = {"contents": contents}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
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
                    for part in _parts(event):
                        if part:
                            yield part


def _parts(event: dict) -> list[str]:
    try:
        return [p.get("text", "") for p in event["candidates"][0]["content"]["parts"]]
    except (KeyError, IndexError, TypeError):
        return []
