"use client";

import { ReactNode, useEffect } from "react";

import { fetchAgents, fetchConversations } from "@/lib/api";
import { useStore } from "@/lib/store";

/**
 * App providers. The AG-UI client wiring is isolated in lib/agui.ts, so a later
 * phase can wrap this in the CopilotKit provider with an HttpAgent registered
 * against /agui/run, or point at AgentCore's native AG-UI endpoint, and add the
 * MSAL provider, without touching the components below.
 */
export function Providers({ children }: { children: ReactNode }) {
  const setAgents = useStore((s) => s.setAgents);
  const setConversations = useStore((s) => s.setConversations);

  useEffect(() => {
    fetchAgents().then(setAgents).catch(() => setAgents([]));
    fetchConversations().then(setConversations).catch(() => setConversations([]));
  }, [setAgents, setConversations]);

  return <>{children}</>;
}
