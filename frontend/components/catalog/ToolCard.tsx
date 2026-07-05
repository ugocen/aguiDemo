"use client";

import { ToolItem } from "@/lib/store";

export function ToolCard({ item }: { item: ToolItem }) {
  const result = item.result as { answer?: string; matched?: string | null } | null;
  return (
    <div className="card">
      <span className="tool-badge">tool call, {item.name}</span>
      <div className="card-label">arguments</div>
      <div className="mono">{JSON.stringify(item.args ?? {}, null, 2)}</div>
      <div className="card-label" style={{ marginTop: 10 }}>
        {item.status === "running" ? "running..." : "result"}
      </div>
      {item.status === "done" && result && (
        <div className="mono">{result.answer ?? JSON.stringify(result, null, 2)}</div>
      )}
    </div>
  );
}
