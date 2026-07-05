"use client";

import { AgentList } from "@/components/sidebar/AgentList";
import { HistoryList } from "@/components/sidebar/HistoryList";
import { ChatArea } from "@/components/chat/ChatArea";
import { CanvasPanel } from "@/components/canvas/CanvasPanel";
import { useStore } from "@/lib/store";

export default function WorkspacePage() {
  const doc = useStore((s) => s.doc);
  const canvasActive = doc.title !== "Untitled" || doc.content.length > 0;

  return (
    <div className="workspace">
      <aside className="sidebar">
        <AgentList />
        <HistoryList />
      </aside>
      <main className="main">
        <ChatArea />
        {canvasActive && <CanvasPanel />}
      </main>
    </div>
  );
}
