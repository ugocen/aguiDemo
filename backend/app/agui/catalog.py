from typing import Any

LOOKUP_TOOL = "lookupKnowledge"
SUGGESTED_QUESTIONS_TOOL = "renderSuggestedQuestions"
APPROVAL_TOOL = "requestApproval"


def tool_catalog() -> list[dict[str, Any]]:
    """Frontend-tool schemas the backend expects to be declared in RunAgentInput.

    The frontend registers matching handlers with useCopilotAction, so the
    names and parameters agree on both sides. The backend advertises these so a
    run can discover what the client can render, nothing is hardcoded on either
    end beyond this shared contract.
    """
    return [
        {
            "name": SUGGESTED_QUESTIONS_TOOL,
            "description": "Render a set of suggested follow-up questions as clickable chips.",
            "parameters": {
                "type": "object",
                "properties": {
                    "questions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Short follow-up prompts to offer the user.",
                    }
                },
                "required": ["questions"],
            },
        },
        {
            "name": LOOKUP_TOOL,
            "description": "Look up a fact in the demo knowledge base and render the result as a card.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The lookup query."}
                },
                "required": ["query"],
            },
        },
        {
            "name": APPROVAL_TOOL,
            "description": "Ask the user to approve or reject a proposed action before continuing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "The action awaiting approval."},
                    "detail": {"type": "string", "description": "Context for the decision."},
                },
                "required": ["action"],
            },
        },
    ]
