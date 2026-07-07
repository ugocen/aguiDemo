from collections.abc import AsyncIterator

from ag_ui.core import RunAgentInput

from app.agent.events import (
    AgentEvent,
    ReasoningDelta,
    StateDelta,
    StepFinished,
    StepStarted,
    TextDelta,
    ToolCallStarted,
)
from app.agui.catalog import (
    CHART_TOOL,
    FOLLOWUP_TOOL,
    QUIZ_TOOL,
    SUGGESTED_QUESTIONS_TOOL,
)
from agents._common import call_id, tokens


class MathCoachAgent:
    """Adaptive mental-math practice for kids that tracks progress.

    Showcases agentic_generative_ui (interactive quiz) with shared_state
    (score and level drive the difficulty of the next question).
    """

    id = "math-coach"
    name = "Math Coach"
    description = "Adaptive mental-math practice that tracks progress"
    mode = "scenario"

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        state = input.state if isinstance(input.state, dict) else {}
        quiz = state.get("quiz") or {}
        level = int(quiz.get("level", 1))
        score = int(quiz.get("score", 0))
        answered = int(quiz.get("answered", 0))
        streak = int(quiz.get("streak", 0))

        yield StepStarted("Warming up")
        yield ReasoningDelta(
            f"Running score is {score}, so I'll size the next question to level {level}."
        )
        yield ReasoningDelta(
            "A higher score means harder factors; a fresh player stays gentle."
        )
        yield StepFinished("Warming up")

        for token in tokens(
            f"Hi there, math champ! You're on level {level} with a streak of {streak}."
        ):
            yield TextDelta(token)

        yield StateDelta(
            patch=[
                {
                    "op": "add",
                    "path": "/quiz",
                    "value": {
                        "level": level,
                        "score": score,
                        "answered": answered,
                        "streak": streak,
                    },
                }
            ]
        )

        a = level + 6
        b = level + 7
        answer = a * b
        prompt = f"{a} x {b}"
        choices = [answer, answer - 3, answer + 4, answer + 7]

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=QUIZ_TOOL,
            args={
                "prompt": prompt,
                "answer": answer,
                "choices": choices,
                "level": level,
                "index": answered + 1,
                "total": 5,
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=CHART_TOOL,
            args={
                "title": "Your progress",
                "unit": "",
                "series": [
                    {"label": "Correct", "value": score},
                    {"label": "Attempts", "value": answered},
                    {"label": "Streak", "value": streak},
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=FOLLOWUP_TOOL,
            args={
                "title": "Coach tips",
                "items": [
                    {
                        "label": "Estimate first",
                        "detail": "Guess a round number before you compute the exact answer.",
                    },
                    {
                        "label": "Watch the carry",
                        "detail": "When adding partial products, carry tens carefully.",
                    },
                ],
            },
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=SUGGESTED_QUESTIONS_TOOL,
            args={
                "questions": [
                    "Make it harder",
                    "Try division",
                    "Show my streak",
                ]
            },
        )

        for token in tokens("Take your time and give it your best shot. You've got this!"):
            yield TextDelta(token)
