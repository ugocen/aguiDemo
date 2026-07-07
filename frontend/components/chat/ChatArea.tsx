"use client";

import { useEffect, useRef, useState } from "react";

import { RunAgentInput, newId, runAgent } from "@/lib/agui";
import { createConversation, fetchConversations } from "@/lib/api";
import { toolCatalog } from "@/lib/catalog";
import { ReasoningItem, StepsItem, useStore } from "@/lib/store";
import { ApprovalCard } from "@/components/catalog/ApprovalCard";
import { ChartCard } from "@/components/catalog/ChartCard";
import { CitationsCard } from "@/components/catalog/CitationsCard";
import { CommandOutputCard } from "@/components/catalog/CommandOutputCard";
import { DatePickerCard } from "@/components/catalog/DatePickerCard";
import { FollowUpCard } from "@/components/catalog/FollowUpCard";
import { FormCard } from "@/components/catalog/FormCard";
import { HotelsCard } from "@/components/catalog/HotelsCard";
import { QuizCard } from "@/components/catalog/QuizCard";
import { SuggestedQuestions } from "@/components/catalog/SuggestedQuestions";
import { TableCard } from "@/components/catalog/TableCard";
import { ToolCard } from "@/components/catalog/ToolCard";

function StepsStrip({ item }: { item: StepsItem }) {
  return (
    <div className="steps-strip">
      {item.entries.map((s, i) => (
        <span key={i} className={`step-chip ${s.status}`}>
          <span className="step-ic" aria-hidden="true">
            {s.status === "done" ? "✓" : ""}
          </span>
          {s.name}
        </span>
      ))}
    </div>
  );
}

function ReasoningBlock({ item }: { item: ReasoningItem }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`reasoning ${open ? "open" : ""}`}>
      <button className="reasoning-head" onClick={() => setOpen((v) => !v)}>
        <span className="brain" aria-hidden="true">🧠</span>
        {item.done ? "Thought it through" : "Thinking…"}
        <span className="chev" aria-hidden="true">›</span>
      </button>
      {open && <div className="reasoning-body">{item.text}</div>}
    </div>
  );
}

export function ChatArea() {
  const items = useStore((s) => s.items);
  const doc = useStore((s) => s.doc);
  const isRunning = useStore((s) => s.isRunning);
  const threadId = useStore((s) => s.threadId);
  const selectedAgentId = useStore((s) => s.selectedAgentId);
  const pushUser = useStore((s) => s.pushUser);
  const handleEvent = useStore((s) => s.handleEvent);
  const setThread = useStore((s) => s.setThread);
  const setConversations = useStore((s) => s.setConversations);

  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [items, doc]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || isRunning) return;
    setDraft("");

    let tid = threadId;
    if (!tid) {
      const conversation = await createConversation(
        selectedAgentId ?? "local-langgraph",
        trimmed.slice(0, 60),
      );
      tid = conversation?.id ?? newId("thread");
      setThread(tid);
    }

    const history = items
      .filter((item) => item.kind === "user" || item.kind === "assistant")
      .map((item) => ({
        id: item.id,
        role: item.kind as "user" | "assistant",
        content: "text" in item ? item.text : "",
      }));

    pushUser(trimmed);

    const input: RunAgentInput = {
      threadId: tid,
      runId: newId("run"),
      state: useStore.getState().sharedState,
      messages: [...history, { id: newId("u"), role: "user", content: trimmed }],
      tools: toolCatalog(),
      context: [],
      forwardedProps: { agentId: selectedAgentId },
    };

    try {
      await runAgent(input, handleEvent);
    } catch (error) {
      handleEvent({ type: "RUN_ERROR", message: String(error) });
    }

    fetchConversations().then(setConversations).catch(() => undefined);
  }

  const lastUserText = [...items].reverse().find((i) => i.kind === "user");

  return (
    <div className="chat-region">
      <div className="messages" ref={scrollRef}>
        {items.length === 0 && (
          <div className="empty-hint">
            <div className="empty-mark">◈</div>
            Ask the agent anything. Try{" "}
            <em>&quot;explain ag-ui, compare the types, then draft a note and approve&quot;</em> to
            watch reasoning, steps, cards, and a human-in-the-loop, live.
          </div>
        )}
        {items.map((item) => {
          if (item.kind === "user") {
            return (
              <div key={item.id} className="row user">
                <div className="bubble user">{item.text}</div>
                <span className="avatar sm">UG</span>
              </div>
            );
          }
          if (item.kind === "steps") {
            return (
              <div key={item.id} className="row ai">
                <StepsStrip item={item} />
              </div>
            );
          }
          if (item.kind === "reasoning") {
            return (
              <div key={item.id} className="row ai">
                <ReasoningBlock item={item} />
              </div>
            );
          }
          if (item.kind === "assistant") {
            return (
              <div key={item.id} className="row ai">
                <span className="avatar ai-av" aria-hidden="true">✦</span>
                <div className="ai-col">
                  <div className="bubble assistant">{item.text}</div>
                  <div className="msg-actions">
                    <button
                      className="msg-act"
                      onClick={() => navigator.clipboard?.writeText(item.text)}
                    >
                      ⧉ Copy
                    </button>
                    <button className="msg-act" aria-label="Good response">👍</button>
                    <button className="msg-act" aria-label="Bad response">👎</button>
                    <button
                      className="msg-act"
                      onClick={() => lastUserText && send(lastUserText.text)}
                    >
                      ↻ Regenerate
                    </button>
                  </div>
                </div>
              </div>
            );
          }
          if (item.kind === "tool") return <ToolCard key={item.id} item={item} />;
          if (item.kind === "approval") return <ApprovalCard key={item.id} item={item} />;
          if (item.kind === "table") return <TableCard key={item.id} item={item} />;
          if (item.kind === "followup") return <FollowUpCard key={item.id} item={item} />;
          if (item.kind === "chart") return <ChartCard key={item.id} item={item} />;
          if (item.kind === "citations") return <CitationsCard key={item.id} item={item} />;
          if (item.kind === "form") {
            return <FormCard key={item.id} item={item} onSubmit={(text) => send(text)} />;
          }
          if (item.kind === "hotels") {
            return <HotelsCard key={item.id} item={item} onAction={(text) => send(text)} />;
          }
          if (item.kind === "datepicker") {
            return <DatePickerCard key={item.id} item={item} onAction={(text) => send(text)} />;
          }
          if (item.kind === "commandOutput") return <CommandOutputCard key={item.id} item={item} />;
          if (item.kind === "quiz") {
            return <QuizCard key={item.id} item={item} onAction={(text) => send(text)} />;
          }
          return (
            <div key={item.id} className="row ai">
              <div className="bubble assistant error-banner">{item.message}</div>
            </div>
          );
        })}
        <SuggestedQuestions onPick={(question) => send(question)} />
      </div>

      <div className="composer">
        <div className="composer-inner">
          <button className="composer-clip" aria-label="Attach">⧉</button>
          <textarea
            value={draft}
            placeholder="Message the agent… ask for a table, a chart, or a draft"
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                send(draft);
              }
            }}
          />
          <button
            className="composer-send"
            disabled={isRunning}
            aria-label="Send"
            onClick={() => send(draft)}
          >
            {isRunning ? "…" : "→"}
          </button>
        </div>
        <div className="composer-hint">
          Streaming typed AG-UI events over SSE · reasoning &amp; steps shown live
        </div>
      </div>
    </div>
  );
}
