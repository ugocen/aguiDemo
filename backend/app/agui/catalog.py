from typing import Any

LOOKUP_TOOL = "lookupKnowledge"
SUGGESTED_QUESTIONS_TOOL = "renderSuggestedQuestions"
APPROVAL_TOOL = "requestApproval"
TABLE_TOOL = "renderTable"
FOLLOWUP_TOOL = "renderFollowUp"
CHART_TOOL = "renderChart"


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
        {
            "name": TABLE_TOOL,
            "description": "Render structured tabular data as a table card.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Table caption."},
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Column headers.",
                    },
                    "rows": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "string"}},
                        "description": "Row values, aligned to columns.",
                    },
                },
                "required": ["columns", "rows"],
            },
        },
        {
            "name": FOLLOWUP_TOOL,
            "description": "Render follow-up information or next steps as a list card.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Section heading."},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {"type": "string"},
                                "detail": {"type": "string"},
                            },
                            "required": ["label"],
                        },
                        "description": "Follow-up entries.",
                    },
                },
                "required": ["items"],
            },
        },
        {
            "name": CHART_TOOL,
            "description": "Render a simple bar chart from labeled numeric series.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Chart caption."},
                    "unit": {"type": "string", "description": "Optional value unit, e.g. %."},
                    "series": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {"type": "string"},
                                "value": {"type": "number"},
                            },
                            "required": ["label", "value"],
                        },
                        "description": "Bars to plot.",
                    },
                },
                "required": ["series"],
            },
        },
    ]
