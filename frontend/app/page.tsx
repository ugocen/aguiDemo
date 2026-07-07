"use client";

import { useState } from "react";

import { AgentList } from "@/components/sidebar/AgentList";
import { HistoryList } from "@/components/sidebar/HistoryList";
import { ChatArea } from "@/components/chat/ChatArea";
import { CanvasPanel } from "@/components/canvas/CanvasPanel";
import { SharedStatePanel } from "@/components/canvas/SharedStatePanel";
import { EventInspector } from "@/components/inspector/EventInspector";
import { CopilotChatArea } from "@/components/copilot/CopilotChatArea";
import { useStore } from "@/lib/store";

const CLIENT_MODE = process.env.NEXT_PUBLIC_CLIENT ?? "custom";

export default function WorkspacePage() {
  const doc = useStore((s) => s.doc);
  const eventCount = useStore((s) => s.eventLog.length);
  const [showInspector, setShowInspector] = useState(false);
  const canvasActive = doc.title !== "Untitled" || doc.content.length > 0;
  const useCopilot = CLIENT_MODE === "copilotkit";

  return (
    <div className="workspace">
      <aside className="sidebar">
        <AgentList />
        <HistoryList />
      </aside>
      <div className="main-col">
        <div className="topbar">
          <div className="brand">
            <span className="brand-glyph" aria-hidden="true">◈</span>
            <span className="brand-text">
              <span className="brand-name">AG-UI Studio</span>
              <span className="brand-sub">
                {useCopilot ? "CopilotKit client" : "custom client · streaming over SSE"}
              </span>
            </span>
          </div>
          <div className="topbar-right">
            {!useCopilot && (
              <button className="btn ghost" onClick={() => setShowInspector((v) => !v)}>
                {showInspector ? "Hide events" : `Events${eventCount ? ` · ${eventCount}` : ""}`}
              </button>
            )}
            <div className="user-chip">
              <span className="avatar sm">UG</span>
              <span className="user-meta">
                <span className="user-name">Ugur Gocen</span>
                <span className="user-role">Platform Admin</span>
              </span>
            </div>
          </div>
        </div>
        {useCopilot ? (
          <CopilotChatArea />
        ) : (
          <>
            <main className="main">
              <ChatArea />
              {canvasActive && <CanvasPanel />}
              <SharedStatePanel />
            </main>
            {showInspector && <EventInspector onClose={() => setShowInspector(false)} />}
          </>
        )}
      </div>
    </div>
  );
}
