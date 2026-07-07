"use client";

import { useState } from "react";

import { QUIZ_TOOL } from "@/lib/catalog";
import { QuizItem, useStore } from "@/lib/store";

/**
 * Interactive practice question (agentic generative UI). Answering it checks the
 * answer locally, updates the shared training state (score, streak, level), and
 * reports back so the agent adapts the next question's difficulty.
 */
export function QuizCard({
  item,
  onAction,
}: {
  item: QuizItem;
  onAction: (text: string) => void;
}) {
  const patchSharedState = useStore((s) => s.patchSharedState);
  const sharedState = useStore((s) => s.sharedState);
  const isRunning = useStore((s) => s.isRunning);
  const [free, setFree] = useState("");
  const [given, setGiven] = useState<number | null>(null);

  const answered = given !== null;
  const correct = answered && given === item.answer;

  function submit(value: number) {
    if (answered || isRunning || Number.isNaN(value)) return;
    setGiven(value);
    const isRight = value === item.answer;
    const quiz = (sharedState.quiz ?? {}) as Record<string, unknown>;
    const total = Number(quiz.answered ?? 0) + 1;
    const score = Number(quiz.score ?? 0) + (isRight ? 1 : 0);
    const streak = isRight ? Number(quiz.streak ?? 0) + 1 : 0;
    const level = Math.max(1, Math.min(10, Math.round(score / 2) + 1));
    patchSharedState([
      { op: "replace", path: "/quiz/answered", value: total },
      { op: "replace", path: "/quiz/score", value: score },
      { op: "replace", path: "/quiz/streak", value: streak },
      { op: "replace", path: "/quiz/level", value: level },
    ]);
    onAction(
      `Answered ${item.prompt} = ${value} (${isRight ? "correct" : "wrong"}). Score ${score}, level ${level}.`,
    );
  }

  return (
    <div className="card quiz-card">
      <span className="tool-badge">quiz, {QUIZ_TOOL}</span>
      <div className="quiz-meta">
        <span className="quiz-level">Level {item.level}</span>
        <span className="quiz-count">
          Q{item.index}/{item.total}
        </span>
      </div>
      <div className="quiz-prompt">{item.prompt} = ?</div>
      {item.choices.length > 0 ? (
        <div className="quiz-choices">
          {item.choices.map((choice) => (
            <button
              key={choice}
              className={`quiz-choice ${
                answered
                  ? choice === item.answer
                    ? "right"
                    : choice === given
                      ? "wrong"
                      : ""
                  : ""
              }`}
              disabled={answered || isRunning}
              onClick={() => submit(choice)}
            >
              {choice}
            </button>
          ))}
        </div>
      ) : (
        <div className="quiz-free">
          <input
            className="form-input"
            type="number"
            placeholder="Your answer"
            value={free}
            disabled={answered}
            onChange={(e) => setFree(e.target.value)}
          />
          <button
            className="btn approve"
            disabled={answered || isRunning || free === ""}
            onClick={() => submit(Number(free))}
          >
            Check
          </button>
        </div>
      )}
      {answered && (
        <div className={`quiz-result ${correct ? "right" : "wrong"}`}>
          {correct ? "Correct! 🎉" : `Not quite — it's ${item.answer}.`}
        </div>
      )}
    </div>
  );
}
