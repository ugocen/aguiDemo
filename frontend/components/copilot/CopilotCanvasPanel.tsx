"use client";

import { useCoAgent } from "@copilotkit/react-core";

import { COPILOT_AGENT_NAME } from "@/app/api/copilotkit/agentName";

interface CanvasState {
  document?: { title?: string; content?: string };
}

/**
 * Canvas bound to the CopilotKit agent's shared state. The backend emits
 * STATE_SNAPSHOT / STATE_DELTA, CopilotKit exposes it through useCoAgent, and
 * this panel renders the document live while the run streams.
 */
export function CopilotCanvasPanel() {
  const { state } = useCoAgent<CanvasState>({
    name: COPILOT_AGENT_NAME,
    initialState: { document: { title: "Untitled", content: "" } },
  });

  const document = state?.document ?? { title: "Untitled", content: "" };
  const active = (document.title && document.title !== "Untitled") || Boolean(document.content);
  if (!active) return null;

  return (
    <div className="canvas-panel">
      <div className="canvas-header">
        <input value={document.title ?? ""} readOnly aria-label="Document title" />
      </div>
      <div className="canvas-body">
        <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.6 }}>{document.content}</div>
      </div>
    </div>
  );
}
