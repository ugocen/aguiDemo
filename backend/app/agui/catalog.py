from typing import Any

LOOKUP_TOOL = "lookupKnowledge"
SUGGESTED_QUESTIONS_TOOL = "renderSuggestedQuestions"
APPROVAL_TOOL = "requestApproval"
TABLE_TOOL = "renderTable"
FOLLOWUP_TOOL = "renderFollowUp"
CHART_TOOL = "renderChart"
CITATIONS_TOOL = "renderCitations"
FORM_TOOL = "renderForm"
HOTELS_TOOL = "renderHotels"
DATE_PICKER_TOOL = "renderDatePicker"
COMMAND_OUTPUT_TOOL = "renderCommandOutput"
QUIZ_TOOL = "renderQuiz"
EDIT_DOCUMENT_TOOL = "editDocument"


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
        {
            "name": CITATIONS_TOOL,
            "description": "Render a list of sources with titles, links, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Section heading."},
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "url": {"type": "string"},
                                "snippet": {"type": "string"},
                            },
                            "required": ["title"],
                        },
                        "description": "Cited sources.",
                    },
                },
                "required": ["sources"],
            },
        },
        {
            "name": FORM_TOOL,
            "description": "Ask the user for structured input by rendering a form.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Form heading."},
                    "submitLabel": {"type": "string", "description": "Submit button text."},
                    "fields": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "label": {"type": "string"},
                                "type": {"type": "string", "description": "text, email, or number."},
                                "placeholder": {"type": "string"},
                            },
                            "required": ["name", "label"],
                        },
                        "description": "Fields to collect.",
                    },
                },
                "required": ["fields"],
            },
        },
        {
            "name": HOTELS_TOOL,
            "description": (
                "Render clickable hotel result cards the user can select. Selecting one "
                "updates the shared booking state (the cart)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Results heading."},
                    "hotels": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "area": {"type": "string", "description": "District or area."},
                                "rating": {"type": "number", "description": "Star rating 0-5."},
                                "pricePerNight": {"type": "number"},
                                "currency": {"type": "string", "description": "e.g. TRY, EUR."},
                                "seaside": {"type": "boolean", "description": "On the seafront."},
                                "tursabApproved": {
                                    "type": "boolean",
                                    "description": "Holds a valid TURSAB licence.",
                                },
                                "tags": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["name", "area", "pricePerNight"],
                        },
                        "description": "Hotels to offer.",
                    },
                },
                "required": ["hotels"],
            },
        },
        {
            "name": DATE_PICKER_TOOL,
            "description": (
                "Render a check-in/check-out date picker. Confirming the dates updates the "
                "shared booking state (the cart)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Picker heading."},
                    "nights": {"type": "number", "description": "Suggested number of nights."},
                    "checkIn": {"type": "string", "description": "Default check-in (YYYY-MM-DD)."},
                    "checkOut": {"type": "string", "description": "Default check-out (YYYY-MM-DD)."},
                },
                "required": [],
            },
        },
        {
            "name": COMMAND_OUTPUT_TOOL,
            "description": (
                "Render the streamed output of a backend command (Terraform, kubectl, bash) "
                "as a terminal card."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Card heading."},
                    "command": {"type": "string", "description": "The command that ran."},
                    "lines": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "stream": {
                                    "type": "string",
                                    "description": "stdout or stderr.",
                                },
                                "text": {"type": "string"},
                            },
                            "required": ["text"],
                        },
                        "description": "Output lines in order.",
                    },
                    "exitCode": {"type": "number", "description": "Process exit code."},
                },
                "required": ["command", "lines"],
            },
        },
        {
            "name": QUIZ_TOOL,
            "description": (
                "Render an interactive practice question. Answering it updates the shared "
                "training state (score, streak, level) so the agent can adapt difficulty."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "The question, e.g. '7 x 8'."},
                    "answer": {"type": "number", "description": "The correct answer."},
                    "choices": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Optional multiple-choice options; omit for free input.",
                    },
                    "level": {"type": "number", "description": "Difficulty level 1-10."},
                    "index": {"type": "number", "description": "Question number in the set."},
                    "total": {"type": "number", "description": "Total questions in the set."},
                },
                "required": ["prompt", "answer"],
            },
        },
        {
            "name": EDIT_DOCUMENT_TOOL,
            "description": (
                "Write or revise the shared canvas document. Provide a title and/or the full "
                "content; the canvas updates live via shared state."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Document title."},
                    "content": {
                        "type": "string",
                        "description": "Full document body (replaces the current content).",
                    },
                },
                "required": [],
            },
        },
    ]
