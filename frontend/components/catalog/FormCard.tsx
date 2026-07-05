"use client";

import { useState } from "react";

import { FormItem, useStore } from "@/lib/store";

/**
 * Structured input card. The agent asks for input via renderForm; the user
 * fills it and submits. In the custom client the submitted values are sent back
 * as the next user turn, so the conversation continues with the collected data.
 */
export function FormCard({ item, onSubmit }: { item: FormItem; onSubmit: (text: string) => void }) {
  const setFormSubmitted = useStore((s) => s.setFormSubmitted);
  const isRunning = useStore((s) => s.isRunning);
  const [values, setValues] = useState<Record<string, string>>({});

  const submitted = item.submitted !== null;

  function submit() {
    if (submitted || isRunning) return;
    const filled: Record<string, string> = {};
    for (const field of item.fields) {
      filled[field.name] = values[field.name] ?? "";
    }
    setFormSubmitted(item.id, filled);
    const summary = item.fields
      .map((field) => `${field.label}: ${filled[field.name] || "(empty)"}`)
      .join(", ");
    onSubmit(`Form submitted — ${summary}`);
  }

  return (
    <div className="card">
      <span className="tool-badge">form, renderForm</span>
      {item.title && <div style={{ fontWeight: 600, marginBottom: 10 }}>{item.title}</div>}
      {item.fields.map((field) => (
        <div key={field.name} className="form-row">
          <label className="form-label">{field.label}</label>
          <input
            className="form-input"
            type={field.type === "number" ? "number" : field.type === "email" ? "email" : "text"}
            placeholder={field.placeholder}
            disabled={submitted}
            value={submitted ? (item.submitted?.[field.name] ?? "") : (values[field.name] ?? "")}
            onChange={(event) =>
              setValues((prev) => ({ ...prev, [field.name]: event.target.value }))
            }
          />
        </div>
      ))}
      {submitted ? (
        <div style={{ color: "var(--ok)" }}>Submitted</div>
      ) : (
        <button className="btn approve" disabled={isRunning} onClick={submit}>
          {item.submitLabel || "Submit"}
        </button>
      )}
    </div>
  );
}
