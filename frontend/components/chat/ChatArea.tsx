"use client";

import { useEffect, useRef, useState } from "react";

import { RunAgentInput, newId, runAgent } from "@/lib/agui";
import { createConversation, fetchConversations } from "@/lib/api";
import { toolCatalog } from "@/lib/catalog";
import { useStore } from "@/lib/store";
import { ApprovalCard } from "@/components/catalog/ApprovalCard";
import { FollowUpCard } from "@/components/catalog/FollowUpCard";
import { SuggestedQuestions } from "@/components/catalog/SuggestedQuestions";
import { TableCard } from "@/components/catalog/TableCard";
import { ToolCard } from "@/components/catalog/ToolCard";

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
      state: { document: doc },
      messages: [...history, { id: newId("u"), role: "user", content: trimmed }],
      tools: toolCatalog(),
      context: [],
      forwardedProps: {},
    };

    try {
      await runAgent(input, handleEvent);
    } catch (error) {
      handleEvent({ type: "RUN_ERROR", message: String(error) });
    }

    fetchConversations().then(setConversations).catch(() => undefined);
  }

  return (
    <div className="chat-region">
      <div className="messages" ref={scrollRef}>
        {items.length === 0 && (
          <div className="empty-hint">
            Ask something. Try &quot;explain ag-ui and draft a note then approve&quot; to see all four
            capabilities.
          </div>
        )}
        {items.map((item) => {
          if (item.kind === "user") {
            return (
              <div key={item.id} className="message-row">
                <div className="bubble user">{item.text}</div>
              </div>
            );
          }
          if (item.kind === "assistant") {
            return (
              <div key={item.id} className="message-row">
                <div className="bubble assistant">{item.text}</div>
              </div>
            );
          }
          if (item.kind === "tool") {
            return <ToolCard key={item.id} item={item} />;
          }
          if (item.kind === "approval") {
            return <ApprovalCard key={item.id} item={item} />;
          }
          if (item.kind === "table") {
            return <TableCard key={item.id} item={item} />;
          }
          if (item.kind === "followup") {
            return <FollowUpCard key={item.id} item={item} />;
          }
          return (
            <div key={item.id} className="message-row">
              <div className="bubble assistant error-banner">{item.message}</div>
            </div>
          );
        })}
        <SuggestedQuestions onPick={(question) => send(question)} />
      </div>

      <div className="composer">
        <div className="composer-inner">
          <textarea
            value={draft}
            placeholder="Message the agent..."
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                send(draft);
              }
            }}
          />
          <button className="btn" disabled={isRunning} onClick={() => send(draft)}>
            {isRunning ? "..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}
