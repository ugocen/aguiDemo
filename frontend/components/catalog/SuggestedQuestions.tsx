"use client";

import { useStore } from "@/lib/store";

export function SuggestedQuestions({ onPick }: { onPick: (question: string) => void }) {
  const suggestedQuestions = useStore((s) => s.suggestedQuestions);
  if (suggestedQuestions.length === 0) return null;

  return (
    <div className="message-row">
      <div className="card-label">suggested</div>
      {suggestedQuestions.map((question) => (
        <span key={question} className="chip" onClick={() => onPick(question)}>
          {question}
        </span>
      ))}
    </div>
  );
}
