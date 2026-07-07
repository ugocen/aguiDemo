import { getBearerToken } from "./auth";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export interface AgentDescriptor {
  id: string;
  name: string;
  description: string;
}

export interface ConversationSummary {
  id: string;
  user_id: string;
  agent_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface StoredMessage {
  id: string;
  role: string;
  content: string;
  tool_events_json: unknown;
  created_at: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: StoredMessage[];
}

async function authorized(path: string, init: RequestInit = {}): Promise<Response> {
  const token = await getBearerToken();
  return fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init.headers ?? {}),
    },
  });
}

export async function fetchAgents(): Promise<AgentDescriptor[]> {
  const response = await authorized("/agents");
  if (!response.ok) return [];
  return response.json();
}

export async function fetchConversations(): Promise<ConversationSummary[]> {
  const response = await authorized("/conversations");
  if (!response.ok) return [];
  return response.json();
}

export async function fetchConversation(id: string): Promise<ConversationDetail | null> {
  const response = await authorized(`/conversations/${id}`);
  if (!response.ok) return null;
  return response.json();
}

export async function createConversation(
  agentId: string,
  title: string,
): Promise<ConversationSummary | null> {
  const response = await authorized("/conversations", {
    method: "POST",
    body: JSON.stringify({ agent_id: agentId, title }),
  });
  if (!response.ok) return null;
  return response.json();
}

export interface RunSummary {
  run_id: string;
  thread_id: string;
  user: string;
  count: number;
  modified: number;
}

export async function fetchRuns(): Promise<RunSummary[]> {
  const response = await authorized("/agui/runs");
  if (!response.ok) return [];
  const data = await response.json();
  return (data.runs ?? []) as RunSummary[];
}

/** Returns the recorded AG-UI events for a run, ready to feed back through the store. */
export async function fetchRunLog(runId: string): Promise<Record<string, unknown>[]> {
  const response = await authorized(`/agui/runs/${encodeURIComponent(runId)}/log`);
  if (!response.ok) return [];
  const data = await response.json();
  const entries = (data.events ?? []) as Array<{ event?: Record<string, unknown> }>;
  return entries.map((entry) => entry.event ?? {}).filter((event) => "type" in event);
}
