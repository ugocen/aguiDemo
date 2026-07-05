import { create } from "zustand";

import { AgentDescriptor, ConversationSummary, StoredMessage } from "./api";
import { AguiEvent, JsonPatchOp, newId } from "./agui";
import {
  APPROVAL_TOOL,
  CHART_TOOL,
  FOLLOWUP_TOOL,
  LOOKUP_TOOL,
  SUGGESTED_QUESTIONS_TOOL,
  TABLE_TOOL,
} from "./catalog";

export interface DocumentState {
  title: string;
  content: string;
}

export interface UserItem {
  kind: "user";
  id: string;
  text: string;
}

export interface AssistantItem {
  kind: "assistant";
  id: string;
  text: string;
}

export interface ToolItem {
  kind: "tool";
  id: string;
  name: string;
  args: Record<string, unknown> | null;
  result: unknown;
  status: "running" | "done";
}

export interface ApprovalItem {
  kind: "approval";
  id: string;
  runId: string;
  action: string;
  detail: string;
  decision: { approved: boolean; reason: string } | null;
}

export interface TableItem {
  kind: "table";
  id: string;
  title: string;
  columns: string[];
  rows: string[][];
}

export interface FollowUpEntry {
  label: string;
  detail: string;
}

export interface FollowUpItem {
  kind: "followup";
  id: string;
  title: string;
  entries: FollowUpEntry[];
}

export interface ChartPoint {
  label: string;
  value: number;
}

export interface ChartItem {
  kind: "chart";
  id: string;
  title: string;
  unit: string;
  points: ChartPoint[];
}

export interface ErrorItem {
  kind: "error";
  id: string;
  message: string;
}

export type ChatItem =
  | UserItem
  | AssistantItem
  | ToolItem
  | ApprovalItem
  | TableItem
  | FollowUpItem
  | ChartItem
  | ErrorItem;

export type EventCategory = "lifecycle" | "text" | "tool" | "state" | "other";

export interface EventLogEntry {
  seq: number;
  type: string;
  category: EventCategory;
  detail: string;
  count: number;
}

interface StoreState {
  agents: AgentDescriptor[];
  conversations: ConversationSummary[];
  selectedAgentId: string | null;
  threadId: string | null;
  items: ChatItem[];
  doc: DocumentState;
  suggestedQuestions: string[];
  isRunning: boolean;
  currentRunId: string | null;
  pendingApprovalId: string | null;

  eventLog: EventLogEntry[];
  eventSeq: number;

  toolNames: Record<string, string>;
  toolArgs: Record<string, string>;

  setAgents: (agents: AgentDescriptor[]) => void;
  setConversations: (conversations: ConversationSummary[]) => void;
  selectAgent: (id: string) => void;
  setThread: (id: string | null) => void;
  resetChat: () => void;
  loadMessages: (messages: StoredMessage[]) => void;
  pushUser: (text: string) => void;
  setSuggestedQuestions: (questions: string[]) => void;
  handleEvent: (event: AguiEvent) => void;
  setApprovalDecision: (id: string, approved: boolean, reason: string) => void;
  clearEventLog: () => void;
}

const EVENT_CATEGORY: Record<string, EventCategory> = {
  RUN_STARTED: "lifecycle",
  RUN_FINISHED: "lifecycle",
  RUN_ERROR: "lifecycle",
  TEXT_MESSAGE_START: "text",
  TEXT_MESSAGE_CONTENT: "text",
  TEXT_MESSAGE_END: "text",
  TOOL_CALL_START: "tool",
  TOOL_CALL_ARGS: "tool",
  TOOL_CALL_END: "tool",
  TOOL_CALL_RESULT: "tool",
  STATE_SNAPSHOT: "state",
  STATE_DELTA: "state",
};

function categoryOf(type: string): EventCategory {
  return EVENT_CATEGORY[type] ?? "other";
}

function summarize(event: AguiEvent): string {
  switch (event.type) {
    case "RUN_STARTED":
      return `run ${event.runId ?? ""}`;
    case "TEXT_MESSAGE_CONTENT":
      return typeof event.delta === "string" ? JSON.stringify(event.delta) : "";
    case "TOOL_CALL_START":
      return event.toolCallName ?? "";
    case "TOOL_CALL_RESULT":
      return (event.content ?? "").slice(0, 60);
    case "STATE_DELTA":
      return Array.isArray(event.delta)
        ? (event.delta as JsonPatchOp[]).map((op) => op.path).join(", ")
        : "";
    case "RUN_ERROR":
      return event.message ?? "";
    default:
      return "";
  }
}

const EMPTY_DOC: DocumentState = { title: "Untitled", content: "" };

function applyPatch(doc: DocumentState, patch: JsonPatchOp[]): DocumentState {
  const next: DocumentState = { ...doc };
  for (const op of patch) {
    const parts = op.path.split("/").filter(Boolean);
    if (parts[0] !== "document" || parts.length < 2) continue;
    const key = parts[1];
    if (key !== "title" && key !== "content") continue;
    if (op.op === "remove") {
      next[key] = "";
    } else {
      next[key] = String(op.value ?? "");
    }
  }
  return next;
}

function safeParse(value: string): Record<string, unknown> {
  try {
    return JSON.parse(value) as Record<string, unknown>;
  } catch {
    return {};
  }
}

export const useStore = create<StoreState>((set, get) => ({
  agents: [],
  conversations: [],
  selectedAgentId: null,
  threadId: null,
  items: [],
  doc: { ...EMPTY_DOC },
  suggestedQuestions: [],
  isRunning: false,
  currentRunId: null,
  pendingApprovalId: null,
  eventLog: [],
  eventSeq: 0,
  toolNames: {},
  toolArgs: {},

  setAgents: (agents) =>
    set((s) => ({ agents, selectedAgentId: s.selectedAgentId ?? agents[0]?.id ?? null })),
  setConversations: (conversations) => set({ conversations }),
  selectAgent: (id) => set({ selectedAgentId: id }),
  setThread: (id) => set({ threadId: id }),

  resetChat: () =>
    set({
      items: [],
      doc: { ...EMPTY_DOC },
      suggestedQuestions: [],
      pendingApprovalId: null,
      currentRunId: null,
      eventLog: [],
      eventSeq: 0,
    }),

  clearEventLog: () => set({ eventLog: [], eventSeq: 0 }),

  loadMessages: (messages) =>
    set(() => {
      const items: ChatItem[] = messages.map((m) =>
        m.role === "user"
          ? { kind: "user", id: m.id, text: m.content }
          : { kind: "assistant", id: m.id, text: m.content },
      );
      return { items, doc: { ...EMPTY_DOC }, suggestedQuestions: [], pendingApprovalId: null };
    }),

  pushUser: (text) =>
    set((s) => ({
      items: [...s.items, { kind: "user", id: newId("u"), text }],
      suggestedQuestions: [],
    })),

  setSuggestedQuestions: (questions) => set({ suggestedQuestions: questions }),

  setApprovalDecision: (id, approved, reason) =>
    set((s) => ({
      items: s.items.map((item) =>
        item.kind === "approval" && item.id === id
          ? { ...item, decision: { approved, reason } }
          : item,
      ),
    })),

  handleEvent: (event) => {
    const state = get();

    set((s) => {
      const last = s.eventLog[s.eventLog.length - 1];
      if (event.type === "TEXT_MESSAGE_CONTENT" && last && last.type === "TEXT_MESSAGE_CONTENT") {
        const merged = [...s.eventLog];
        merged[merged.length - 1] = { ...last, count: last.count + 1, detail: summarize(event) };
        return { eventLog: merged };
      }
      const entry: EventLogEntry = {
        seq: s.eventSeq + 1,
        type: event.type,
        category: categoryOf(event.type),
        detail: summarize(event),
        count: 1,
      };
      const next = [...s.eventLog, entry];
      return { eventLog: next.slice(-300), eventSeq: s.eventSeq + 1 };
    });

    switch (event.type) {
      case "RUN_STARTED":
        set({ isRunning: true, currentRunId: event.runId ?? null });
        break;

      case "STATE_SNAPSHOT": {
        const snapshot = (event.snapshot ?? {}) as { document?: DocumentState };
        set({ doc: { ...EMPTY_DOC, ...(snapshot.document ?? {}) } });
        break;
      }

      case "STATE_DELTA":
        set({ doc: applyPatch(state.doc, (event.delta as JsonPatchOp[]) ?? []) });
        break;

      case "TEXT_MESSAGE_START":
        set((s) => ({
          items: [...s.items, { kind: "assistant", id: event.messageId ?? newId("a"), text: "" }],
        }));
        break;

      case "TEXT_MESSAGE_CONTENT":
        set((s) => ({
          items: s.items.map((item) =>
            item.kind === "assistant" && item.id === event.messageId
              ? { ...item, text: item.text + (typeof event.delta === "string" ? event.delta : "") }
              : item,
          ),
        }));
        break;

      case "TOOL_CALL_START": {
        const id = event.toolCallId ?? newId("call");
        const name = event.toolCallName ?? "";
        set((s) => {
          const toolNames = { ...s.toolNames, [id]: name };
          if (name === LOOKUP_TOOL) {
            return {
              toolNames,
              items: [
                ...s.items,
                { kind: "tool", id, name, args: null, result: null, status: "running" },
              ],
            };
          }
          if (name === APPROVAL_TOOL) {
            return {
              toolNames,
              currentRunId: s.currentRunId,
              pendingApprovalId: id,
              items: [
                ...s.items,
                {
                  kind: "approval",
                  id,
                  runId: s.currentRunId ?? "",
                  action: "",
                  detail: "",
                  decision: null,
                },
              ],
            };
          }
          if (name === TABLE_TOOL) {
            return {
              toolNames,
              items: [...s.items, { kind: "table", id, title: "", columns: [], rows: [] }],
            };
          }
          if (name === FOLLOWUP_TOOL) {
            return {
              toolNames,
              items: [...s.items, { kind: "followup", id, title: "", entries: [] }],
            };
          }
          if (name === CHART_TOOL) {
            return {
              toolNames,
              items: [...s.items, { kind: "chart", id, title: "", unit: "", points: [] }],
            };
          }
          return { toolNames };
        });
        break;
      }

      case "TOOL_CALL_ARGS": {
        const id = event.toolCallId ?? "";
        set((s) => ({
          toolArgs: {
            ...s.toolArgs,
            [id]: (s.toolArgs[id] ?? "") + (typeof event.delta === "string" ? event.delta : ""),
          },
        }));
        break;
      }

      case "TOOL_CALL_END": {
        const id = event.toolCallId ?? "";
        const name = state.toolNames[id];
        const args = safeParse(state.toolArgs[id] ?? "{}");
        if (name === SUGGESTED_QUESTIONS_TOOL) {
          const questions = Array.isArray(args.questions) ? (args.questions as string[]) : [];
          set({ suggestedQuestions: questions });
        } else if (name === LOOKUP_TOOL) {
          set((s) => ({
            items: s.items.map((item) =>
              item.kind === "tool" && item.id === id ? { ...item, args } : item,
            ),
          }));
        } else if (name === APPROVAL_TOOL) {
          set((s) => ({
            items: s.items.map((item) =>
              item.kind === "approval" && item.id === id
                ? {
                    ...item,
                    action: String(args.action ?? "Approve this action"),
                    detail: String(args.detail ?? ""),
                  }
                : item,
            ),
          }));
        } else if (name === TABLE_TOOL) {
          const columns = Array.isArray(args.columns) ? (args.columns as string[]) : [];
          const rows = Array.isArray(args.rows) ? (args.rows as string[][]) : [];
          set((s) => ({
            items: s.items.map((item) =>
              item.kind === "table" && item.id === id
                ? { ...item, title: String(args.title ?? ""), columns, rows }
                : item,
            ),
          }));
        } else if (name === FOLLOWUP_TOOL) {
          const entries = Array.isArray(args.items)
            ? (args.items as Array<Record<string, unknown>>).map((entry) => ({
                label: String(entry.label ?? ""),
                detail: String(entry.detail ?? ""),
              }))
            : [];
          set((s) => ({
            items: s.items.map((item) =>
              item.kind === "followup" && item.id === id
                ? { ...item, title: String(args.title ?? ""), entries }
                : item,
            ),
          }));
        } else if (name === CHART_TOOL) {
          const points = Array.isArray(args.series)
            ? (args.series as Array<Record<string, unknown>>).map((point) => ({
                label: String(point.label ?? ""),
                value: Number(point.value ?? 0),
              }))
            : [];
          set((s) => ({
            items: s.items.map((item) =>
              item.kind === "chart" && item.id === id
                ? { ...item, title: String(args.title ?? ""), unit: String(args.unit ?? ""), points }
                : item,
            ),
          }));
        }
        break;
      }

      case "TOOL_CALL_RESULT": {
        const id = event.toolCallId ?? "";
        const result = safeParse(event.content ?? "{}");
        set((s) => ({
          items: s.items.map((item) => {
            if (item.kind === "tool" && item.id === id) {
              return { ...item, result, status: "done" as const };
            }
            if (item.kind === "approval" && item.id === id && item.decision === null) {
              return {
                ...item,
                decision: {
                  approved: Boolean(result.approved),
                  reason: String(result.reason ?? ""),
                },
              };
            }
            return item;
          }),
          pendingApprovalId: s.pendingApprovalId === id ? null : s.pendingApprovalId,
        }));
        break;
      }

      case "RUN_FINISHED":
        set({ isRunning: false, pendingApprovalId: null });
        break;

      case "RUN_ERROR":
        set((s) => ({
          isRunning: false,
          pendingApprovalId: null,
          items: [
            ...s.items,
            { kind: "error", id: newId("err"), message: event.message ?? "Run error" },
          ],
        }));
        break;

      default:
        break;
    }
  },
}));
