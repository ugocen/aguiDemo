import { getBearerToken } from "./auth";
import { ToolSchema } from "./catalog";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export interface AguiMessage {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
}

export interface JsonPatchOp {
  op: "add" | "replace" | "remove";
  path: string;
  value?: unknown;
}

export interface RunAgentInput {
  threadId: string;
  runId: string;
  state: Record<string, unknown>;
  messages: AguiMessage[];
  tools: ToolSchema[];
  context: unknown[];
  forwardedProps: Record<string, unknown>;
}

export interface AguiEvent {
  type: string;
  messageId?: string;
  delta?: string | JsonPatchOp[];
  toolCallId?: string;
  toolCallName?: string;
  snapshot?: Record<string, unknown>;
  content?: string;
  role?: string;
  runId?: string;
  threadId?: string;
  message?: string;
  stepName?: string;
}

/**
 * The only place the frontend talks to the AG-UI transport. Swapping to
 * CopilotKit's HttpAgent or AgentCore's native endpoint stays contained here.
 */
export async function runAgent(
  input: RunAgentInput,
  onEvent: (event: AguiEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const token = await getBearerToken();
  const response = await fetch(`${BACKEND_URL}/agui/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
    signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`run failed: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      for (const line of frame.split("\n")) {
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (!payload) continue;
        try {
          onEvent(JSON.parse(payload) as AguiEvent);
        } catch {
          // ignore keepalive comments and malformed frames
        }
      }
    }
  }
}

export async function resumeRun(
  runId: string,
  approved: boolean,
  reason: string,
): Promise<void> {
  const token = await getBearerToken();
  await fetch(`${BACKEND_URL}/agui/resume`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ run_id: runId, approved, reason }),
  });
}

export function newId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}
