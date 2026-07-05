"use client";

import { useState } from "react";

import { AgentList } from "@/components/sidebar/AgentList";
import { HistoryList } from "@/components/sidebar/HistoryList";
import { ChatArea } from "@/components/chat/ChatArea";
import { CanvasPanel } from "@/components/canvas/CanvasPanel";
import { EventInspector } from "@/components/inspector/EventInspector";
import { useStore } from "@/lib/store";

export default function WorkspacePage() {
  const doc = useStore((s) => s.doc);
  const eventCount = useStore((s) => s.eventLog.length);
  const [showInspector, setShowInspector] = useState(false);
  const canvasActive = doc.title !== "Untitled" || doc.content.length > 0;

  return (
    <div className="workspace">
      <aside className="sidebar">
        <AgentList />
        <HistoryList />
      </aside>
      <div className="main-col">
        <div className="topbar">
          <span className="topbar-title">AG-UI Workspace</span>
          <button className="btn" onClick={() => setShowInspector((v) => !v)}>
            {showInspector ? "Hide events" : `Show events${eventCount ? ` (${eventCount})` : ""}`}
          </button>
        </div>
        <main className="main">
          <ChatArea />
          {canvasActive && <CanvasPanel />}
        </main>
        {showInspector && <EventInspector onClose={() => setShowInspector(false)} />}
      </div>
    </div>
  );
}
