from dataclasses import dataclass, field
from typing import Any


@dataclass
class TextDelta:
    text: str


@dataclass
class ReasoningDelta:
    """A chunk of the model's reasoning / thinking, shown before the answer."""

    text: str


@dataclass
class StepStarted:
    name: str


@dataclass
class StepFinished:
    name: str


@dataclass
class ToolCallStarted:
    tool_call_id: str
    name: str
    args: dict[str, Any]


@dataclass
class ToolCallCompleted:
    tool_call_id: str
    result: Any


@dataclass
class DocumentSnapshot:
    document: dict[str, Any]


@dataclass
class DocumentDelta:
    patch: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ApprovalRequested:
    """Human-in-the-loop request.

    The agent yields this and receives the decision back through the generator
    ``asend`` channel, so only the translator ever emits protocol events.
    """

    tool_call_id: str
    name: str
    args: dict[str, Any]


AgentEvent = (
    TextDelta
    | ReasoningDelta
    | StepStarted
    | StepFinished
    | ToolCallStarted
    | ToolCallCompleted
    | DocumentSnapshot
    | DocumentDelta
    | ApprovalRequested
)
