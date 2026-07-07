"use client";

import { COMMAND_OUTPUT_TOOL } from "@/lib/catalog";
import { CommandOutputItem } from "@/lib/store";

/**
 * Backend tool rendering: the streamed output of a backend command (Terraform,
 * kubectl, bash) rendered as a terminal card, with stderr highlighted and the
 * exit code as a status badge.
 */
export function CommandOutputCard({ item }: { item: CommandOutputItem }) {
  const ok = item.exitCode === 0 || item.exitCode === null;
  return (
    <div className="card">
      <span className="tool-badge">command, {COMMAND_OUTPUT_TOOL}</span>
      {item.title && <div style={{ fontWeight: 600, marginBottom: 8 }}>{item.title}</div>}
      <div className="terminal">
        <div className="terminal-bar">
          <span className="terminal-dot r" />
          <span className="terminal-dot y" />
          <span className="terminal-dot g" />
          <span className="terminal-cmd">$ {item.command}</span>
        </div>
        <pre className="terminal-body">
          {item.lines.map((line, i) => (
            <span key={i} className={`term-line ${line.stream === "stderr" ? "err" : ""}`}>
              {line.text}
              {"\n"}
            </span>
          ))}
        </pre>
        {item.exitCode !== null && (
          <div className={`terminal-exit ${ok ? "ok" : "bad"}`}>exit {item.exitCode}</div>
        )}
      </div>
    </div>
  );
}
