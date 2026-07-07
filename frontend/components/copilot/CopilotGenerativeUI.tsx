"use client";

import { useState } from "react";

import { useCopilotAction } from "@copilotkit/react-core";

import { resumeRun } from "@/lib/agui";
import {
  APPROVAL_TOOL,
  CHART_TOOL,
  CITATIONS_TOOL,
  COMMAND_OUTPUT_TOOL,
  DATE_PICKER_TOOL,
  FOLLOWUP_TOOL,
  FORM_TOOL,
  HOTELS_TOOL,
  LOOKUP_TOOL,
  QUIZ_TOOL,
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
  runId?: string;
}

interface ChartArgs {
  title?: string;
  unit?: string;
  series?: Array<{ label?: string; value?: number }>;
}

interface CitationsArgs {
  title?: string;
  sources?: Array<{ title?: string; url?: string; snippet?: string }>;
}

interface FormField {
  name?: string;
  label?: string;
  type?: string;
  placeholder?: string;
}

interface FormArgs {
  title?: string;
  submitLabel?: string;
  fields?: FormField[];
}

interface HotelArgs {
  title?: string;
  hotels?: Array<{
    name?: string;
    area?: string;
    rating?: number;
    pricePerNight?: number;
    currency?: string;
    seaside?: boolean;
    tursabApproved?: boolean;
    tags?: string[];
  }>;
}

interface DatePickerArgs {
  title?: string;
  nights?: number;
  checkIn?: string;
  checkOut?: string;
}

interface CommandArgs {
  title?: string;
  command?: string;
  lines?: Array<{ stream?: string; text?: string }>;
  exitCode?: number;
}

interface QuizArgs {
  prompt?: string;
  answer?: number;
  choices?: number[];
  level?: number;
  index?: number;
  total?: number;
}

function CopilotFormRender({
  args,
  respond,
}: {
  args: FormArgs;
  respond?: (value: unknown) => void;
}) {
  const fields = args.fields ?? [];
  const [values, setValues] = useState<Record<string, string>>({});
  const [done, setDone] = useState(false);

  function submit() {
    if (done || !respond) return;
    setDone(true);
    respond(values);
  }

  return (
    <div className="card">
      <span className="tool-badge">form, {FORM_TOOL}</span>
      {args.title && <div style={{ fontWeight: 600, marginBottom: 10 }}>{args.title}</div>}
      {fields.map((field) => (
        <div key={field.name} className="form-row">
          <label className="form-label">{field.label}</label>
          <input
            className="form-input"
            type={field.type === "number" ? "number" : field.type === "email" ? "email" : "text"}
            placeholder={field.placeholder}
            disabled={done}
            value={values[field.name ?? ""] ?? ""}
            onChange={(event) =>
              setValues((prev) => ({ ...prev, [field.name ?? ""]: event.target.value }))
            }
          />
        </div>
      ))}
      {done ? (
        <div style={{ color: "var(--ok)" }}>Submitted</div>
      ) : (
        <button className="btn approve" onClick={submit}>
          {args.submitLabel || "Submit"}
        </button>
      )}
    </div>
  );
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
    name: CHART_TOOL,
    available: "disabled",
    render: (props: { args: ChartArgs }) => {
      const { title, unit = "", series = [] } = props.args ?? {};
      const values = series.map((point) => Number(point.value ?? 0));
      const max = Math.max(1, ...values);
      return (
        <div className="card">
          <span className="tool-badge">chart, {CHART_TOOL}</span>
          {title && <div style={{ fontWeight: 600, marginBottom: 8 }}>{title}</div>}
          {series.map((point, index) => (
            <div key={index} className="copilot-bar-row">
              <span className="copilot-bar-label">{point.label}</span>
              <span className="copilot-bar-track">
                <span
                  className="copilot-bar-fill"
                  style={{ width: `${Math.round((Number(point.value ?? 0) / max) * 100)}%` }}
                />
              </span>
              <span className="copilot-bar-value">
                {point.value}
                {unit}
              </span>
            </div>
          ))}
        </div>
      );
    },
  });

  useCopilotAction({
    name: CITATIONS_TOOL,
    available: "disabled",
    render: (props: { args: CitationsArgs }) => {
      const { title, sources = [] } = props.args ?? {};
      return (
        <div className="card">
          <span className="tool-badge">citations, {CITATIONS_TOOL}</span>
          {title && <div style={{ fontWeight: 600, marginBottom: 8 }}>{title}</div>}
          <ol className="citations-list">
            {sources.map((source, index) => (
              <li key={index}>
                {source.url ? (
                  <a href={source.url} target="_blank" rel="noreferrer" className="citation-title">
                    {source.title}
                  </a>
                ) : (
                  <span className="citation-title">{source.title}</span>
                )}
                {source.snippet && <div className="citation-snippet">{source.snippet}</div>}
              </li>
            ))}
          </ol>
        </div>
      );
    },
  });

  useCopilotAction({
    name: FORM_TOOL,
    available: "disabled",
    renderAndWaitForResponse: (props: {
      args: FormArgs;
      respond?: (value: unknown) => void;
    }) => <CopilotFormRender args={props.args ?? {}} respond={props.respond} />,
  });

  useCopilotAction({
    name: HOTELS_TOOL,
    available: "disabled",
    render: (props: { args: HotelArgs }) => {
      const { title, hotels = [] } = props.args ?? {};
      return (
        <div className="card">
          <span className="tool-badge">hotels, {HOTELS_TOOL}</span>
          {title && <div style={{ fontWeight: 600, marginBottom: 8 }}>{title}</div>}
          <div className="hotel-grid">
            {hotels.map((hotel, index) => (
              <div key={index} className="hotel-card">
                <div className="hotel-top">
                  <span className="hotel-name">{hotel.name}</span>
                  {hotel.rating ? <span className="hotel-rating">★ {hotel.rating}</span> : null}
                </div>
                <div className="hotel-area">{hotel.area}</div>
                <div className="hotel-bottom">
                  <span className="hotel-price">
                    {hotel.pricePerNight} {hotel.currency}
                    <span className="hotel-per"> / night</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    },
  });

  useCopilotAction({
    name: DATE_PICKER_TOOL,
    available: "disabled",
    render: (props: { args: DatePickerArgs }) => {
      const { title, nights, checkIn, checkOut } = props.args ?? {};
      return (
        <div className="card">
          <span className="tool-badge">dates, {DATE_PICKER_TOOL}</span>
          {title && <div style={{ fontWeight: 600, marginBottom: 8 }}>{title}</div>}
          <div className="datepick-row">
            <label className="datepick-field">
              <span className="datepick-label">Check-in</span>
              <input type="date" className="form-input" defaultValue={checkIn} />
            </label>
            <label className="datepick-field">
              <span className="datepick-label">Check-out</span>
              <input type="date" className="form-input" defaultValue={checkOut} />
            </label>
          </div>
          {nights ? <div className="datepick-nights">{nights} nights</div> : null}
        </div>
      );
    },
  });

  useCopilotAction({
    name: COMMAND_OUTPUT_TOOL,
    available: "disabled",
    render: (props: { args: CommandArgs }) => {
      const { title, command, lines = [], exitCode } = props.args ?? {};
      return (
        <div className="card">
          <span className="tool-badge">command, {COMMAND_OUTPUT_TOOL}</span>
          {title && <div style={{ fontWeight: 600, marginBottom: 8 }}>{title}</div>}
          <div className="terminal">
            <div className="terminal-bar">
              <span className="terminal-cmd">$ {command}</span>
            </div>
            <pre className="terminal-body">
              {lines.map((line, index) => (
                <span key={index} className={`term-line ${line.stream === "stderr" ? "err" : ""}`}>
                  {line.text}
                  {"\n"}
                </span>
              ))}
            </pre>
            {exitCode !== undefined && (
              <div className={`terminal-exit ${exitCode === 0 ? "ok" : "bad"}`}>exit {exitCode}</div>
            )}
          </div>
        </div>
      );
    },
  });

  useCopilotAction({
    name: QUIZ_TOOL,
    available: "disabled",
    render: (props: { args: QuizArgs }) => {
      const { prompt, choices = [], level, index, total } = props.args ?? {};
      return (
        <div className="card quiz-card">
          <span className="tool-badge">quiz, {QUIZ_TOOL}</span>
          <div className="quiz-meta">
            <span className="quiz-level">Level {level ?? 1}</span>
            <span className="quiz-count">
              Q{index ?? 1}/{total ?? 1}
            </span>
          </div>
          <div className="quiz-prompt">{prompt} = ?</div>
          <div className="quiz-choices">
            {choices.map((choice) => (
              <span key={choice} className="quiz-choice">
                {choice}
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
      const { action, detail, runId } = props.args ?? {};
      const disabled = props.status === "complete" || !props.respond;
      const decide = (approved: boolean, reason: string) => {
        if (runId) {
          void resumeRun(runId, approved, reason);
        }
        props.respond?.({ approved, reason });
      };
      return (
        <div className="card">
          <span className="tool-badge">approval required</span>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>{action || "Approve this action?"}</div>
          {detail && <div style={{ color: "var(--muted)", marginBottom: 10 }}>{detail}</div>}
          <div style={{ display: "flex", gap: 8 }}>
            <button
              className="btn approve"
              disabled={disabled}
              onClick={() => decide(true, "approved by user")}
            >
              Approve
            </button>
            <button
              className="btn reject"
              disabled={disabled}
              onClick={() => decide(false, "rejected by user")}
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
