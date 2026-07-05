"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

import { COPILOT_AGENT_NAME } from "@/app/api/copilotkit/agentName";
import { CopilotGenerativeUI } from "./CopilotGenerativeUI";

/**
 * CopilotKit client surface. The CopilotKit provider talks to the AG-UI backend
 * through the /api/copilotkit runtime route (which registers an HttpAgent against
 * /agui/run). CopilotChat renders the conversation and the generative UI cards.
 */
export function CopilotChatArea() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent={COPILOT_AGENT_NAME}>
      <CopilotGenerativeUI />
      <div className="chat-region">
        <CopilotChat
          className="copilot-chat"
          labels={{
            title: "AG-UI Agent",
            initial:
              'Ask something. Try "explain ag-ui, compare the types, next steps, draft a note then approve".',
          }}
        />
      </div>
    </CopilotKit>
  );
}
