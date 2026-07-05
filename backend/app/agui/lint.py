from typing import Any


def _event_type(entry: dict[str, Any]) -> str:
    if "type" in entry:
        return entry["type"]
    return entry.get("event", {}).get("type", "")


def _event_body(entry: dict[str, Any]) -> dict[str, Any]:
    if "event" in entry and isinstance(entry["event"], dict):
        return entry["event"]
    return entry


def lint_event_stream(events: list[dict[str, Any]]) -> list[str]:
    """Lint a recorded AG-UI event stream for pairing and ordering.

    Accepts either raw protocol event dicts or capture lines wrapping the event
    under an ``event`` key. Returns a list of human readable problems, empty
    when the stream is well formed.
    """
    problems: list[str] = []
    if not events:
        return ["empty stream"]

    types = [_event_type(e) for e in events]

    if types[0] != "RUN_STARTED":
        problems.append(f"first event is {types[0]}, expected RUN_STARTED")
    if types.count("RUN_STARTED") != 1:
        problems.append(f"expected exactly one RUN_STARTED, found {types.count('RUN_STARTED')}")

    terminal = {"RUN_FINISHED", "RUN_ERROR"}
    if types[-1] not in terminal:
        problems.append(f"last event is {types[-1]}, expected RUN_FINISHED or RUN_ERROR")
    terminal_count = sum(1 for t in types if t in terminal)
    if terminal_count != 1:
        problems.append(f"expected exactly one terminal event, found {terminal_count}")
    for index, t in enumerate(types):
        if t in terminal and index != len(types) - 1:
            problems.append(f"terminal event {t} at position {index} is not last")

    open_text: str | None = None
    for entry in events:
        t = _event_type(entry)
        body = _event_body(entry)
        if t == "TEXT_MESSAGE_START":
            if open_text is not None:
                problems.append("TEXT_MESSAGE_START while another text message is open")
            open_text = body.get("messageId")
        elif t == "TEXT_MESSAGE_CONTENT":
            if open_text is None:
                problems.append("TEXT_MESSAGE_CONTENT outside an open text message")
            elif body.get("messageId") != open_text:
                problems.append("TEXT_MESSAGE_CONTENT id does not match open text message")
        elif t == "TEXT_MESSAGE_END":
            if open_text is None:
                problems.append("TEXT_MESSAGE_END without an open text message")
            elif body.get("messageId") != open_text:
                problems.append("TEXT_MESSAGE_END id does not match open text message")
            open_text = None
    if open_text is not None:
        problems.append("text message left open at end of stream")

    tool_state: dict[str, str] = {}
    for entry in events:
        t = _event_type(entry)
        body = _event_body(entry)
        tool_id = body.get("toolCallId")
        if t == "TOOL_CALL_START":
            if tool_id in tool_state:
                problems.append(f"TOOL_CALL_START for already started tool {tool_id}")
            tool_state[tool_id] = "started"
        elif t == "TOOL_CALL_ARGS":
            if tool_state.get(tool_id) != "started":
                problems.append(f"TOOL_CALL_ARGS before START for tool {tool_id}")
        elif t == "TOOL_CALL_END":
            if tool_state.get(tool_id) != "started":
                problems.append(f"TOOL_CALL_END before START for tool {tool_id}")
            tool_state[tool_id] = "ended"
        elif t == "TOOL_CALL_RESULT":
            if tool_id not in tool_state:
                problems.append(f"TOOL_CALL_RESULT for unknown tool {tool_id}")

    return problems
