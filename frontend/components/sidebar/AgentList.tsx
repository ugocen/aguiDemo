"use client";

import { useStore } from "@/lib/store";

export function AgentList() {
  const agents = useStore((s) => s.agents);
  const selectedAgentId = useStore((s) => s.selectedAgentId);
  const selectAgent = useStore((s) => s.selectAgent);

  return (
    <div className="sidebar-section">
      <div className="sidebar-title">Agents</div>
      {agents.length === 0 && <div className="empty-hint" style={{ marginTop: 8, fontSize: 13 }}>No agents.</div>}
      {agents.map((agent) => (
        <div
          key={agent.id}
          className={`list-item ${agent.id === selectedAgentId ? "active" : ""}`}
          onClick={() => selectAgent(agent.id)}
        >
          {agent.name}
          {agent.description && <div className="subtitle">{agent.description}</div>}
        </div>
      ))}
    </div>
  );
}
