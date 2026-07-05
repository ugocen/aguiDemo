from typing import Any

_KNOWLEDGE_BASE: dict[str, str] = {
    "ag-ui": "AG-UI is an open, event-based protocol that streams typed JSON events "
    "(lifecycle, text, tool calls, state, custom) from an agent backend to a "
    "frontend over Server-Sent Events.",
    "sse": "Server-Sent Events is a one-way streaming transport over HTTP where the "
    "server pushes text/event-stream frames to the client.",
    "agentcore": "Amazon Bedrock AgentCore is the managed runtime where the demo agents "
    "are deployed in later phases.",
    "copilotkit": "CopilotKit is the React AG-UI client used for chat rendering, "
    "generative UI, and human-in-the-loop.",
}


def lookup_knowledge(query: str) -> dict[str, Any]:
    """Demo backend tool, a simple deterministic lookup over a tiny knowledge base."""
    normalized = query.lower().strip()
    for key, value in _KNOWLEDGE_BASE.items():
        if key in normalized:
            return {"query": query, "matched": key, "answer": value}
    return {
        "query": query,
        "matched": None,
        "answer": "No exact match in the demo knowledge base. Try asking about AG-UI, SSE, "
        "AgentCore, or CopilotKit.",
    }
