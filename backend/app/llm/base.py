import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


class LLMError(RuntimeError):
    pass


@dataclass
class TextChunk:
    text: str


@dataclass
class ReasoningChunk:
    text: str


@dataclass
class ToolCallChunk:
    id: str
    name: str
    arguments: dict[str, Any]


StreamChunk = TextChunk | ReasoningChunk | ToolCallChunk


@runtime_checkable
class LLMClient(Protocol):
    """Vendor-agnostic streaming chat interface.

    Every provider (Marketplace gateway, OpenAI, Anthropic, Gemini) exposes the
    same methods, so agents and the translator never depend on a specific vendor:
    ``stream_completion`` yields plain text, and ``stream_chat`` also lets the
    model call the frontend tools (it decides which card to render).
    """

    async def stream_completion(self, messages: list[dict]) -> AsyncIterator[str]:
        ...

    def stream_chat(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> AsyncIterator[StreamChunk]:
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


def tool_call_id() -> str:
    return f"call_{uuid.uuid4().hex[:8]}"
