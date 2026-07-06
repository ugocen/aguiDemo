import json
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from ag_ui.core import (
    BaseEvent,
    EventType,
    ReasoningEndEvent,
    ReasoningMessageContentEvent,
    ReasoningMessageEndEvent,
    ReasoningMessageStartEvent,
    ReasoningStartEvent,
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StateDeltaEvent,
    StateSnapshotEvent,
    StepFinishedEvent,
    StepStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
)

from app.agent.base import initial_state
from app.agent.events import (
    ApprovalRequested,
    DocumentDelta,
    DocumentSnapshot,
    ReasoningDelta,
    StepFinished,
    StepStarted,
    TextDelta,
    ToolCallCompleted,
    ToolCallStarted,
)
from app.agui.resume import ApprovalDecision, resume_registry
from app.agui.run_capture import RunCapture
from app.logging.setup import get_logger

log = get_logger("translator")


@dataclass
class RunResult:
    assistant_text: str = ""
    tool_events: list[dict[str, Any]] = field(default_factory=list)
    final_state: dict[str, Any] = field(default_factory=dict)
    errored: bool = False
    error_message: str = ""


def _apply_patch(state: dict[str, Any], patch: list[dict[str, Any]]) -> None:
    for op in patch:
        path = op.get("path", "")
        parts = [p for p in path.split("/") if p != ""]
        if not parts:
            continue
        target = state
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        leaf = parts[-1]
        action = op.get("op")
        if action in ("add", "replace"):
            target[leaf] = op.get("value")
        elif action == "remove":
            target.pop(leaf, None)


class Translator:
    """The single place AG-UI events are emitted.

    It enforces, in one place, run lifecycle pairing, text message pairing with a
    consistent id, the tool-call event sequence, state snapshot and deltas for
    the canvas, and the human-in-the-loop suspend and resume.
    """

    def __init__(
        self,
        *,
        input: RunAgentInput,
        agent: Any,
        user_id: str,
        capture: RunCapture | None = None,
    ) -> None:
        self._input = input
        self._agent = agent
        self._user_id = user_id
        self._capture = capture
        self._state = initial_state(input)
        self._text_open = False
        self._text_message_id: str | None = None
        self._reasoning_open = False
        self._reasoning_message_id: str | None = None
        self.result = RunResult()

    def _emit(self, event: BaseEvent) -> BaseEvent:
        payload = event.model_dump(by_alias=True, exclude_none=True)
        if self._capture is not None:
            self._capture.record(event.type.value, payload)
        log.info(
            "agui_event",
            event_type=event.type.value,
            run_id=self._input.run_id,
            thread_id=self._input.thread_id,
            user=self._user_id,
        )
        return event

    def _open_text(self) -> BaseEvent | None:
        if self._text_open:
            return None
        self._text_message_id = f"msg_{uuid.uuid4().hex[:8]}"
        self._text_open = True
        return self._emit(
            TextMessageStartEvent(
                type=EventType.TEXT_MESSAGE_START,
                message_id=self._text_message_id,
                role="assistant",
            )
        )

    def _close_text(self) -> BaseEvent | None:
        if not self._text_open or self._text_message_id is None:
            return None
        event = self._emit(
            TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=self._text_message_id)
        )
        self._text_open = False
        return event

    def _open_reasoning(self) -> list[BaseEvent]:
        if self._reasoning_open:
            return []
        self._reasoning_message_id = f"rsn_{uuid.uuid4().hex[:8]}"
        self._reasoning_open = True
        return [
            self._emit(
                ReasoningStartEvent(
                    type=EventType.REASONING_START, message_id=self._reasoning_message_id
                )
            ),
            self._emit(
                ReasoningMessageStartEvent(
                    type=EventType.REASONING_MESSAGE_START,
                    message_id=self._reasoning_message_id,
                    role="reasoning",
                )
            ),
        ]

    def _close_reasoning(self) -> list[BaseEvent]:
        if not self._reasoning_open or self._reasoning_message_id is None:
            return []
        mid = self._reasoning_message_id
        self._reasoning_open = False
        return [
            self._emit(ReasoningMessageEndEvent(type=EventType.REASONING_MESSAGE_END, message_id=mid)),
            self._emit(ReasoningEndEvent(type=EventType.REASONING_END, message_id=mid)),
        ]

    async def stream(self) -> AsyncIterator[BaseEvent]:
        run_id = self._input.run_id
        thread_id = self._input.thread_id
        yield self._emit(
            RunStartedEvent(type=EventType.RUN_STARTED, thread_id=thread_id, run_id=run_id)
        )
        yield self._emit(
            StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot=self._state)
        )

        generator = self._agent.run(self._input)
        to_send: Any = None
        try:
            while True:
                try:
                    agent_event = await generator.asend(to_send)
                except StopAsyncIteration:
                    break
                to_send = None

                if not isinstance(agent_event, ReasoningDelta):
                    for ev in self._close_reasoning():
                        yield ev

                if isinstance(agent_event, ReasoningDelta):
                    for ev in self._open_reasoning():
                        yield ev
                    yield self._emit(
                        ReasoningMessageContentEvent(
                            type=EventType.REASONING_MESSAGE_CONTENT,
                            message_id=self._reasoning_message_id,
                            delta=agent_event.text,
                        )
                    )

                elif isinstance(agent_event, StepStarted):
                    yield self._emit(
                        StepStartedEvent(type=EventType.STEP_STARTED, step_name=agent_event.name)
                    )

                elif isinstance(agent_event, StepFinished):
                    yield self._emit(
                        StepFinishedEvent(type=EventType.STEP_FINISHED, step_name=agent_event.name)
                    )

                elif isinstance(agent_event, TextDelta):
                    opened = self._open_text()
                    if opened is not None:
                        yield opened
                    self.result.assistant_text += agent_event.text
                    yield self._emit(
                        TextMessageContentEvent(
                            type=EventType.TEXT_MESSAGE_CONTENT,
                            message_id=self._text_message_id,
                            delta=agent_event.text,
                        )
                    )

                elif isinstance(agent_event, ToolCallStarted):
                    closed = self._close_text()
                    if closed is not None:
                        yield closed
                    yield self._emit(
                        ToolCallStartEvent(
                            type=EventType.TOOL_CALL_START,
                            tool_call_id=agent_event.tool_call_id,
                            tool_call_name=agent_event.name,
                        )
                    )
                    yield self._emit(
                        ToolCallArgsEvent(
                            type=EventType.TOOL_CALL_ARGS,
                            tool_call_id=agent_event.tool_call_id,
                            delta=json.dumps(agent_event.args),
                        )
                    )
                    yield self._emit(
                        ToolCallEndEvent(
                            type=EventType.TOOL_CALL_END, tool_call_id=agent_event.tool_call_id
                        )
                    )
                    self.result.tool_events.append(
                        {"type": "call", "tool_call_id": agent_event.tool_call_id, "name": agent_event.name, "args": agent_event.args}
                    )

                elif isinstance(agent_event, ToolCallCompleted):
                    yield self._emit(
                        ToolCallResultEvent(
                            type=EventType.TOOL_CALL_RESULT,
                            message_id=f"tmsg_{uuid.uuid4().hex[:8]}",
                            tool_call_id=agent_event.tool_call_id,
                            content=json.dumps(agent_event.result),
                            role="tool",
                        )
                    )
                    self.result.tool_events.append(
                        {"type": "result", "tool_call_id": agent_event.tool_call_id, "result": agent_event.result}
                    )

                elif isinstance(agent_event, DocumentSnapshot):
                    self._state.update(agent_event.document)
                    yield self._emit(
                        StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot=self._state)
                    )

                elif isinstance(agent_event, DocumentDelta):
                    _apply_patch(self._state, agent_event.patch)
                    yield self._emit(
                        StateDeltaEvent(type=EventType.STATE_DELTA, delta=agent_event.patch)
                    )

                elif isinstance(agent_event, ApprovalRequested):
                    closed = self._close_text()
                    if closed is not None:
                        yield closed
                    yield self._emit(
                        ToolCallStartEvent(
                            type=EventType.TOOL_CALL_START,
                            tool_call_id=agent_event.tool_call_id,
                            tool_call_name=agent_event.name,
                        )
                    )
                    approval_args = {**agent_event.args, "runId": run_id}
                    yield self._emit(
                        ToolCallArgsEvent(
                            type=EventType.TOOL_CALL_ARGS,
                            tool_call_id=agent_event.tool_call_id,
                            delta=json.dumps(approval_args),
                        )
                    )
                    yield self._emit(
                        ToolCallEndEvent(
                            type=EventType.TOOL_CALL_END, tool_call_id=agent_event.tool_call_id
                        )
                    )
                    resume_registry.arm(run_id)
                    decision: ApprovalDecision = await resume_registry.wait(run_id)
                    yield self._emit(
                        ToolCallResultEvent(
                            type=EventType.TOOL_CALL_RESULT,
                            message_id=f"tmsg_{uuid.uuid4().hex[:8]}",
                            tool_call_id=agent_event.tool_call_id,
                            content=json.dumps(decision.to_result()),
                            role="tool",
                        )
                    )
                    self.result.tool_events.append(
                        {"type": "approval", "tool_call_id": agent_event.tool_call_id, "decision": decision.to_result()}
                    )
                    to_send = decision

            for ev in self._close_reasoning():
                yield ev
            closed = self._close_text()
            if closed is not None:
                yield closed
            self.result.final_state = self._state
            yield self._emit(
                RunFinishedEvent(type=EventType.RUN_FINISHED, thread_id=thread_id, run_id=run_id)
            )
        except Exception as exc:  # noqa: BLE001
            for ev in self._close_reasoning():
                yield ev
            closed = self._close_text()
            if closed is not None:
                yield closed
            self.result.errored = True
            self.result.error_message = str(exc)
            log.error("run_error", run_id=run_id, error=str(exc))
            yield self._emit(
                RunErrorEvent(type=EventType.RUN_ERROR, message=str(exc))
            )
        finally:
            if self._capture is not None:
                self._capture.close()
