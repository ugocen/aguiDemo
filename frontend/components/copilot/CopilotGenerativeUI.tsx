"use client";

import { useCopilotAction } from "@copilotkit/react-core";

import {
  APPROVAL_TOOL,
  FOLLOWUP_TOOL,
  LOOKUP_TOOL,
  SUGGESTED_QUESTIONS_TOOL,
  TABLE_TOOL,
} from "@/lib/catalog";

interface TableArgs {
  title?: string;
  columns?: string[];
  rows?: string[][];
}

interface FollowUpArgs {
  title?: string;
  items?: Array<{ label?: string; detail?: string }>;
}

interface LookupArgs {
  query?: string;
}

interface ApprovalArgs {
  action?: string;
  detail?: string;
}

/**
 * CopilotKit generative UI. Each agent tool declared in the shared catalog is
 * bound to a render here through useCopilotAction, the CopilotKit way of turning
 * an agent message type into a card. renderAndWaitForResponse implements the
 * human-in-the-loop approval. This component renders nothing itself; CopilotChat
 * renders each card inline when the matching tool call streams in.
 */
export function CopilotGenerativeUI() {
  useCopilotAction({
    name: LOOKUP_TOOL,
    available: "disabled",
    render: (props: { status: string; args: LookupArgs; result?: unknown }) => {
      const result = props.result as { answer?: string } | undefined;
      return (
        <div className="card">
          <span className="tool-badge">tool call, {LOOKUP_TOOL}</span>
          <div className="card-label">arguments</div>
          <div className="mono">{JSON.stringify(props.args ?? {}, null, 2)}</div>
          <div className="card-label" style={{ marginTop: 10 }}>
            {props.status === "complete" ? "result" : "running..."}
          </div>
          {result?.answer && <div className="mono">{result.answer}</div>}
        </div>
      );
    },
  });

  useCopilotAction({
    name: TABLE_TOOL,
    available: "disabled",
    render: (props: { args: TableArgs }) => {
      const { title, columns = [], rows = [] } = props.args ?? {};
      return (
        <div className="card">
          <span className="tool-badge">table, {TABLE_TOOL}</span>
          {title && <div style={{ fontWeight: 600, marginBottom: 8 }}>{title}</div>}
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  {columns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    {row.map((cell, cellIndex) => (
                      <td key={cellIndex}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    },
  });

  useCopilotAction({
    name: FOLLOWUP_TOOL,
    available: "disabled",
    render: (props: { args: FollowUpArgs }) => {
      const { title, items = [] } = props.args ?? {};
      return (
        <div className="card">
          <span className="tool-badge">follow-up, {FOLLOWUP_TOOL}</span>
          {title && <div style={{ fontWeight: 600, marginBottom: 8 }}>{title}</div>}
          <ul className="followup-list">
            {items.map((entry, index) => (
              <li key={index}>
                <span className="followup-label">{entry.label}</span>
                {entry.detail && <span className="followup-detail"> — {entry.detail}</span>}
              </li>
            ))}
          </ul>
        </div>
      );
    },
  });

  useCopilotAction({
    name: SUGGESTED_QUESTIONS_TOOL,
    available: "disabled",
    render: (props: { args: { questions?: string[] } }) => {
      const questions = props.args?.questions ?? [];
      return (
        <div className="card">
          <span className="tool-badge">suggested, {SUGGESTED_QUESTIONS_TOOL}</span>
          <div>
            {questions.map((question) => (
              <span key={question} className="chip">
                {question}
              </span>
            ))}
          </div>
        </div>
      );
    },
  });

  useCopilotAction({
    name: APPROVAL_TOOL,
    available: "disabled",
    renderAndWaitForResponse: (props: {
      status: string;
      args: ApprovalArgs;
      respond?: (value: unknown) => void;
    }) => {
      const { action, detail } = props.args ?? {};
      const disabled = props.status === "complete" || !props.respond;
      return (
        <div className="card">
          <span className="tool-badge">approval required</span>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>{action || "Approve this action?"}</div>
          {detail && <div style={{ color: "var(--muted)", marginBottom: 10 }}>{detail}</div>}
          <div style={{ display: "flex", gap: 8 }}>
            <button
              className="btn approve"
              disabled={disabled}
              onClick={() => props.respond?.({ approved: true, reason: "approved by user" })}
            >
              Approve
            </button>
            <button
              className="btn reject"
              disabled={disabled}
              onClick={() => props.respond?.({ approved: false, reason: "rejected by user" })}
            >
              Reject
            </button>
          </div>
        </div>
      );
    },
  });

  return null;
}
