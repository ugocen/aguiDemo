from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


class LLMError(RuntimeError):
    pass


@runtime_checkable
class LLMClient(Protocol):
    """Vendor-agnostic streaming chat interface.

    Every provider (Marketplace gateway, OpenAI, Anthropic, Gemini) exposes this
    one method, so agents and the translator never depend on a specific vendor.
    """

    async def stream_completion(self, messages: list[dict]) -> AsyncIterator[str]:
        ...


def split_system(messages: list[dict]) -> tuple[str, list[dict]]:
    """Split OpenAI-style messages into a system string and the rest.

    Anthropic and Gemini take the system prompt as a separate top-level field.
    """
    system_parts: list[str] = []
    rest: list[dict] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content", "")
        if role == "system":
            if content:
                system_parts.append(content)
        else:
            rest.append(message)
    return "\n".join(system_parts), rest


def progressive_tokens(text: str) -> list[str]:
    words = text.split(" ")
    return [w if i == 0 else " " + w for i, w in enumerate(words)]
