import { create } from "zustand";

import { AgentDescriptor, ConversationSummary, StoredMessage } from "./api";
import { AguiEvent, JsonPatchOp, newId } from "./agui";
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

export interface CitationSource {
  title: string;
  url: string;
  snippet: string;
}

export interface CitationsItem {
  kind: "citations";
  id: string;
  title: string;
  sources: CitationSource[];
}

export interface FormField {
  name: string;
  label: string;
  type: string;
  placeholder: string;
}

export interface FormItem {
  kind: "form";
  id: string;
  title: string;
  submitLabel: string;
  fields: FormField[];
  submitted: Record<string, string> | null;
}

export interface ErrorItem {
  kind: "error";
  id: string;
  message: string;
}

export interface ReasoningItem {
  kind: "reasoning";
  id: string;
  text: string;
  done: boolean;
}

export interface StepEntry {
  name: string;
  status: "running" | "done";
}

export interface StepsItem {
  kind: "steps";
  id: string;
  entries: StepEntry[];
}

export interface HotelOption {
  id: string;
  name: string;
  area: string;
  rating: number;
  pricePerNight: number;
  currency: string;
  seaside: boolean;
  tursabApproved: boolean;
  tags: string[];
}

export interface HotelsItem {
  kind: "hotels";
  id: string;
  title: string;
  hotels: HotelOption[];
}

export interface DatePickerItem {
  kind: "datepicker";
  id: string;
  title: string;
  nights: number;
  checkIn: string;
  checkOut: string;
}

export interface CommandLine {
  stream: string;
  text: string;
}

export interface CommandOutputItem {
  kind: "commandOutput";
  id: string;
  title: string;
  command: string;
  lines: CommandLine[];
  exitCode: number | null;
}

export interface QuizItem {
  kind: "quiz";
  id: string;
  prompt: string;
  answer: number;
  choices: number[];
  level: number;
  index: number;
  total: number;
}

export type ChatItem =
  | UserItem
  | AssistantItem
  | ReasoningItem
  | StepsItem
  | ToolItem
  | ApprovalItem
  | TableItem
  | FollowUpItem
  | ChartItem
  | CitationsItem
  | FormItem
  | HotelsItem
  | DatePickerItem
  | CommandOutputItem
  | QuizItem
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
  sharedState: Record<string, unknown>;
  suggestedQuestions: string[];
  isRunning: boolean;
  currentRunId: string | null;
  pendingApprovalId: string | null;
  currentStepsId: string | null;

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
  setFormSubmitted: (id: string, values: Record<string, string>) => void;
  patchSharedState: (patch: JsonPatchOp[]) => void;
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
  REASONING_MESSAGE_START: "text",
  REASONING_MESSAGE_CONTENT: "text",
  REASONING_MESSAGE_END: "text",
  STEP_STARTED: "lifecycle",
  STEP_FINISHED: "lifecycle",
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
const EMPTY_STATE: Record<string, unknown> = { document: { ...EMPTY_DOC } };

function docFromState(state: Record<string, unknown>): DocumentState {
  const d = (state.document ?? {}) as Partial<DocumentState>;
  return { title: String(d.title ?? "Untitled"), content: String(d.content ?? "") };
}

/** Apply JSON Patch ops to any shared-state key (cart, quiz, document, ...). */
function applyStatePatch(
  state: Record<string, unknown>,
  patch: JsonPatchOp[],
): Record<string, unknown> {
  const next = JSON.parse(JSON.stringify(state ?? {})) as Record<string, unknown>;
  for (const op of patch) {
    const parts = op.path.split("/").filter(Boolean);
    if (parts.length === 0) continue;
    let target = next;
    for (const part of parts.slice(0, -1)) {
      if (typeof target[part] !== "object" || target[part] === null) {
        target[part] = {};
      }
      target = target[part] as Record<string, unknown>;
    }
    const leaf = parts[parts.length - 1];
    if (op.op === "remove") {
      delete target[leaf];
    } else {
      target[leaf] = op.value;
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
  sharedState: { ...EMPTY_STATE },
  suggestedQuestions: [],
  isRunning: false,
  currentRunId: null,
  pendingApprovalId: null,
  currentStepsId: null,
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
      sharedState: { ...EMPTY_STATE },
      suggestedQuestions: [],
      pendingApprovalId: null,
      currentRunId: null,
      currentStepsId: null,
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
      return {
        items,
        doc: { ...EMPTY_DOC },
        sharedState: { ...EMPTY_STATE },
        suggestedQuestions: [],
        pendingApprovalId: null,
      };
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

  setFormSubmitted: (id, values) =>
    set((s) => ({
      items: s.items.map((item) =>
        item.kind === "form" && item.id === id ? { ...item, submitted: values } : item,
      ),
    })),

  patchSharedState: (patch) =>
    set((s) => {
      const sharedState = applyStatePatch(s.sharedState, patch);
      return { sharedState, doc: docFromState(sharedState) };
    }),

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
        set({ isRunning: true, currentRunId: event.runId ?? null, currentStepsId: null });
        break;

      case "STEP_STARTED":
        set((s) => {
          const name = event.stepName ?? "";
          let stepsId = s.currentStepsId;
          let items = s.items;
          if (stepsId === null) {
            stepsId = newId("steps");
            items = [...items, { kind: "steps", id: stepsId, entries: [] }];
          }
          items = items.map((item) =>
            item.kind === "steps" && item.id === stepsId
              ? { ...item, entries: [...item.entries, { name, status: "running" as const }] }
              : item,
          );
          return { items, currentStepsId: stepsId };
        });
        break;

      case "STEP_FINISHED":
        set((s) => ({
          items: s.items.map((item) => {
            if (item.kind !== "steps" || item.id !== s.currentStepsId) return item;
            const entries = [...item.entries];
            for (let i = entries.length - 1; i >= 0; i--) {
              if (entries[i].name === event.stepName && entries[i].status === "running") {
                entries[i] = { ...entries[i], status: "done" };
                break;
              }
            }
            return { ...item, entries };
          }),
        }));
        break;

      case "REASONING_MESSAGE_START":
        set((s) => ({
          items: [
            ...s.items,
            { kind: "reasoning", id: event.messageId ?? newId("rsn"), text: "", done: false },
          ],
        }));
        break;

      case "REASONING_MESSAGE_CONTENT":
        set((s) => ({
          items: s.items.map((item) =>
            item.kind === "reasoning" && item.id === event.messageId
              ? { ...item, text: item.text + (typeof event.delta === "string" ? event.delta : "") }
              : item,
          ),
        }));
        break;

      case "REASONING_MESSAGE_END":
        set((s) => ({
          items: s.items.map((item) =>
            item.kind === "reasoning" && item.id === event.messageId
              ? { ...item, done: true }
              : item,
          ),
        }));
        break;

      case "STATE_SNAPSHOT": {
        const snapshot = (event.snapshot ?? {}) as Record<string, unknown>;
        set({ sharedState: snapshot, doc: docFromState(snapshot) });
        break;
      }

      case "STATE_DELTA": {
        const sharedState = applyStatePatch(state.sharedState, (event.delta as JsonPatchOp[]) ?? []);
        set({ sharedState, doc: docFromState(sharedState) });
        break;
      }

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
          if (name === CITATIONS_TOOL) {
            return {
              toolNames,
              items: [...s.items, { kind: "citations", id, title: "", sources: [] }],
            };
          }
          if (name === FORM_TOOL) {
            return {
              toolNames,
              items: [
                ...s.items,
                { kind: "form", id, title: "", submitLabel: "Submit", fields: [], submitted: null },
              ],
            };
          }
          if (name === HOTELS_TOOL) {
            return {
              toolNames,
              items: [...s.items, { kind: "hotels", id, title: "", hotels: [] }],
            };
          }
          if (name === DATE_PICKER_TOOL) {
            return {
              toolNames,
              items: [
                ...s.items,
                { kind: "datepicker", id, title: "", nights: 0, checkIn: "", checkOut: "" },
              ],
            };
          }
          if (name === COMMAND_OUTPUT_TOOL) {
            return {
              toolNames,
              items: [
                ...s.items,
                { kind: "commandOutput", id, title: "", command: "", lines: [], exitCode: null },
              ],
            };
          }
          if (name === QUIZ_TOOL) {
            return {
              toolNames,
              items: [
                ...s.items,
                {
                  kind: "quiz",
                  id,
                  prompt: "",
                  answer: 0,
                  choices: [],
                  level: 1,
                  index: 1,
                  total: 1,
                },
              ],
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
        } else if (name === CITATIONS_TOOL) {
          const sources = Array.isArray(args.sources)
            ? (args.sources as Array<Record<string, unknown>>).map((source) => ({
                title: String(source.title ?? ""),
                url: String(source.url ?? ""),
                snippet: String(source.snippet ?? ""),
              }))
            : [];
          set((s) => ({
            items: s.items.map((item) =>
              item.kind === "citations" && item.id === id
                ? { ...item, title: String(args.title ?? ""), sources }
                : item,
            ),
          }));
        } else if (name === FORM_TOOL) {
          const fields = Array.isArray(args.fields)
            ? (args.fields as Array<Record<string, unknown>>).map((field) => ({
                name: String(field.name ?? ""),
                label: String(field.label ?? ""),
                type: String(field.type ?? "text"),
                placeholder: String(field.placeholder ?? ""),
              }))
            : [];
          set((s) => ({
            items: s.items.map((item) =>
              item.kind === "form" && item.id === id
                ? {
                    ...item,
                    title: String(args.title ?? ""),
                    submitLabel: String(args.submitLabel ?? "Submit"),
                    fields,
                  }
                : item,
            ),
          }));
        } else if (name === HOTELS_TOOL) {
          const hotels = Array.isArray(args.hotels)
            ? (args.hotels as Array<Record<string, unknown>>).map((h, i) => ({
                id: String(h.id ?? `h${i}`),
                name: String(h.name ?? ""),
                area: String(h.area ?? ""),
                rating: Number(h.rating ?? 0),
                pricePerNight: Number(h.pricePerNight ?? 0),
                currency: String(h.currency ?? ""),
                seaside: Boolean(h.seaside),
                tursabApproved: Boolean(h.tursabApproved),
                tags: Array.isArray(h.tags) ? (h.tags as unknown[]).map(String) : [],
              }))
            : [];
          set((s) => ({
            items: s.items.map((item) =>
              item.kind === "hotels" && item.id === id
                ? { ...item, title: String(args.title ?? ""), hotels }
                : item,
            ),
          }));
        } else if (name === DATE_PICKER_TOOL) {
          set((s) => ({
            items: s.items.map((item) =>
              item.kind === "datepicker" && item.id === id
                ? {
                    ...item,
                    title: String(args.title ?? "Choose your dates"),
                    nights: Number(args.nights ?? 0),
                    checkIn: String(args.checkIn ?? ""),
                    checkOut: String(args.checkOut ?? ""),
                  }
                : item,
            ),
          }));
        } else if (name === COMMAND_OUTPUT_TOOL) {
          const lines = Array.isArray(args.lines)
            ? (args.lines as Array<Record<string, unknown>>).map((l) => ({
                stream: String(l.stream ?? "stdout"),
                text: String(l.text ?? ""),
              }))
            : [];
          set((s) => ({
            items: s.items.map((item) =>
              item.kind === "commandOutput" && item.id === id
                ? {
                    ...item,
                    title: String(args.title ?? ""),
                    command: String(args.command ?? ""),
                    lines,
                    exitCode: args.exitCode === undefined ? null : Number(args.exitCode),
                  }
                : item,
            ),
          }));
        } else if (name === QUIZ_TOOL) {
          const choices = Array.isArray(args.choices)
            ? (args.choices as unknown[]).map(Number)
            : [];
          set((s) => ({
            items: s.items.map((item) =>
              item.kind === "quiz" && item.id === id
                ? {
                    ...item,
                    prompt: String(args.prompt ?? ""),
                    answer: Number(args.answer ?? 0),
                    choices,
                    level: Number(args.level ?? 1),
                    index: Number(args.index ?? 1),
                    total: Number(args.total ?? 1),
                  }
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
        set({ isRunning: false, pendingApprovalId: null, currentStepsId: null });
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
