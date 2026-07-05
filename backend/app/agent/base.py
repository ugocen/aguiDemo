from typing import Any

from ag_ui.core import RunAgentInput


def latest_user_text(input: RunAgentInput) -> str:
    for message in reversed(input.messages or []):
        if getattr(message, "role", None) == "user":
            content = getattr(message, "content", "") or ""
            if isinstance(content, str):
                return content
    return ""


def default_document_state() -> dict[str, Any]:
    return {"document": {"title": "Untitled", "content": ""}}


def initial_state(input: RunAgentInput) -> dict[str, Any]:
    state = dict(input.state) if isinstance(input.state, dict) else {}
    if "document" not in state:
        state.update(default_document_state())
    return state
