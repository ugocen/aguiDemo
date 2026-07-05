"use client";

import { useState } from "react";

import { resumeRun } from "@/lib/agui";
import { ApprovalItem, useStore } from "@/lib/store";

/**
 * Human-in-the-loop approval. The backend suspends the run after emitting this
 * tool call and waits on POST /agui/resume. The card returns the decision to
 * resume the run; the same open SSE stream then continues.
 */
export function ApprovalCard({ item }: { item: ApprovalItem }) {
  const setApprovalDecision = useStore((s) => s.setApprovalDecision);
  const [busy, setBusy] = useState(false);

  const decided = item.decision !== null;

  async function decide(approved: boolean) {
    if (decided || busy) return;
    setBusy(true);
    const reason = approved ? "approved by user" : "rejected by user";
    setApprovalDecision(item.id, approved, reason);
    try {
      await resumeRun(item.runId, approved, reason);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <span className="tool-badge">approval required</span>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{item.action || "Approve this action?"}</div>
      {item.detail && <div style={{ color: "var(--muted)", marginBottom: 10 }}>{item.detail}</div>}
      {decided ? (
        <div style={{ color: item.decision?.approved ? "var(--ok)" : "var(--danger)" }}>
          {item.decision?.approved ? "Approved" : "Rejected"}
          {item.decision?.reason ? ` — ${item.decision.reason}` : ""}
        </div>
      ) : (
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn approve" disabled={busy} onClick={() => decide(true)}>
            Approve
          </button>
          <button className="btn reject" disabled={busy} onClick={() => decide(false)}>
            Reject
          </button>
        </div>
      )}
    </div>
  );
}
