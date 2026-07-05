"use client";

import { FollowUpItem } from "@/lib/store";

export function FollowUpCard({ item }: { item: FollowUpItem }) {
  return (
    <div className="card">
      <span className="tool-badge">follow-up, renderFollowUp</span>
      {item.title && <div style={{ fontWeight: 600, marginBottom: 8 }}>{item.title}</div>}
      <ul className="followup-list">
        {item.entries.map((entry, index) => (
          <li key={index}>
            <span className="followup-label">{entry.label}</span>
            {entry.detail && <span className="followup-detail"> — {entry.detail}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
