import { create } from "zustand";

import { AgentDescriptor, ConversationSummary, StoredMessage } from "./api";
import { AguiEvent, JsonPatchOp, newId } from "./agui";
import { APPROVAL_TOOL, LOOKUP_TOOL, SUGGESTED_QUESTIONS_TOOL } from "./catalog";

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

export interface ErrorItem {
  kind: "error";
  id: string;
  message: string;
}

export type ChatItem = UserItem | AssistantItem | ToolItem | ApprovalItem | ErrorItem;

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
    }),

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
