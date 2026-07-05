"use client";

import { useEffect, useRef } from "react";

import { EventCategory, useStore } from "@/lib/store";

const CATEGORY_LABEL: Record<EventCategory, string> = {
  lifecycle: "lifecycle",
  text: "text",
  tool: "tool",
  state: "state",
  other: "other",
};

/**
 * Developer view of the AG-UI stream. Every event the agent sends is logged
 * here as it is processed, grouped by category, so it is visible how different
 * message types arrive and how the frontend turns each into UI.
 */
export function EventInspector({ onClose }: { onClose: () => void }) {
  const eventLog = useStore((s) => s.eventLog);
  const clearEventLog = useStore((s) => s.clearEventLog);
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight });
  }, [eventLog]);

  return (
    <div className="inspector">
      <div className="inspector-header">
        <span>Event inspector, {eventLog.length} events</span>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn" onClick={clearEventLog}>
            Clear
          </button>
          <button className="btn" onClick={onClose}>
            Hide
          </button>
        </div>
      </div>
      <div className="inspector-legend">
        {(Object.keys(CATEGORY_LABEL) as EventCategory[]).map((category) => (
          <span key={category} className={`legend-dot cat-${category}`}>
            {CATEGORY_LABEL[category]}
          </span>
        ))}
      </div>
      <div className="inspector-body" ref={bodyRef}>
        {eventLog.length === 0 && <div className="empty-hint" style={{ marginTop: 20, fontSize: 13 }}>No events yet. Send a message.</div>}
        {eventLog.map((entry) => (
          <div key={entry.seq} className={`inspector-row cat-${entry.category}`}>
            <span className="inspector-seq">{entry.seq}</span>
            <span className="inspector-type">{entry.type}</span>
            {entry.count > 1 && <span className="inspector-count">x{entry.count}</span>}
            {entry.detail && <span className="inspector-detail">{entry.detail}</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
