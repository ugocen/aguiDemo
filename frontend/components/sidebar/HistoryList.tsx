"use client";

import { fetchConversation, fetchConversations } from "@/lib/api";
import { useStore } from "@/lib/store";

export function HistoryList() {
  const conversations = useStore((s) => s.conversations);
  const threadId = useStore((s) => s.threadId);
  const setThread = useStore((s) => s.setThread);
  const loadMessages = useStore((s) => s.loadMessages);
  const resetChat = useStore((s) => s.resetChat);
  const setConversations = useStore((s) => s.setConversations);

  async function openConversation(id: string) {
    const detail = await fetchConversation(id);
    if (!detail) return;
    setThread(id);
    loadMessages(detail.messages);
  }

  function startNew() {
    setThread(null);
    resetChat();
    fetchConversations().then(setConversations).catch(() => undefined);
  }

  return (
    <div className="sidebar-section" style={{ flex: 1 }}>
      <button className="new-chat-btn" onClick={startNew}>
        + New conversation
      </button>
      <div className="sidebar-title">History</div>
      {conversations.length === 0 && (
        <div className="empty-hint" style={{ marginTop: 8, fontSize: 13 }}>No conversations yet.</div>
      )}
      {conversations.map((conversation) => (
        <div
          key={conversation.id}
          className={`list-item ${conversation.id === threadId ? "active" : ""}`}
          onClick={() => openConversation(conversation.id)}
        >
          {conversation.title || "Untitled"}
        </div>
      ))}
    </div>
  );
}
