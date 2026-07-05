"use client";

import { useState } from "react";

import { AgentList } from "@/components/sidebar/AgentList";
import { HistoryList } from "@/components/sidebar/HistoryList";
import { ChatArea } from "@/components/chat/ChatArea";
import { CanvasPanel } from "@/components/canvas/CanvasPanel";
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
          <span className="topbar-title">
            AG-UI Workspace, {useCopilot ? "CopilotKit" : "custom"} client
          </span>
          {!useCopilot && (
            <button className="btn" onClick={() => setShowInspector((v) => !v)}>
              {showInspector ? "Hide events" : `Show events${eventCount ? ` (${eventCount})` : ""}`}
            </button>
          )}
        </div>
        {useCopilot ? (
          <main className="main">
            <CopilotChatArea />
          </main>
        ) : (
          <>
            <main className="main">
              <ChatArea />
              {canvasActive && <CanvasPanel />}
            </main>
            {showInspector && <EventInspector onClose={() => setShowInspector(false)} />}
          </>
        )}
      </div>
    </div>
  );
}
