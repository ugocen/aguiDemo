"use client";

import { fetchConversations } from "@/lib/api";
import { useStore } from "@/lib/store";

const ICONS: Record<string, { glyph: string; cls: string }> = {
  "research-assistant": { glyph: "🔍", cls: "ic-research" },
  "doc-writer": { glyph: "📝", cls: "ic-doc" },
  "data-analyst": { glyph: "📊", cls: "ic-data" },
  "support-triage": { glyph: "🛟", cls: "ic-support" },
};

export function AgentList() {
  const agents = useStore((s) => s.agents);
  const selectedAgentId = useStore((s) => s.selectedAgentId);
  const selectAgent = useStore((s) => s.selectAgent);
  const setThread = useStore((s) => s.setThread);
  const resetChat = useStore((s) => s.resetChat);
  const setConversations = useStore((s) => s.setConversations);

  function chooseAgent(id: string) {
    selectAgent(id);
    setThread(null);
    resetChat();
    fetchConversations().then(setConversations).catch(() => undefined);
  }

  return (
    <div className="sidebar-section">
      <div className="sidebar-title">Agents</div>
      {agents.length === 0 && (
        <div className="empty-hint" style={{ marginTop: 8, fontSize: 13 }}>No agents.</div>
      )}
      {agents.map((agent) => {
        const icon = ICONS[agent.id] ?? { glyph: "✦", cls: "ic-data" };
        return (
          <div
            key={agent.id}
            className={`agent-item ${agent.id === selectedAgentId ? "active" : ""}`}
            onClick={() => chooseAgent(agent.id)}
          >
            <span className={`agent-ic ${icon.cls}`} aria-hidden="true">{icon.glyph}</span>
            <span className="agent-meta">
              <span className="agent-name">{agent.name}</span>
              {agent.description && <span className="agent-sub">{agent.description}</span>}
            </span>
          </div>
        );
      })}
    </div>
  );
}
