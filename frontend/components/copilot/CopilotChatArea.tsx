"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

import { COPILOT_AGENT_NAME } from "@/app/api/copilotkit/agentName";
import { useStore } from "@/lib/store";
import { CopilotCanvasPanel } from "./CopilotCanvasPanel";
import { CopilotGenerativeUI } from "./CopilotGenerativeUI";
import { CopilotSharedStatePanel } from "./CopilotSharedStatePanel";

/**
 * CopilotKit client surface. The provider talks to the AG-UI backend through the
 * /api/copilotkit runtime route (an HttpAgent against /agui/run). The selected
 * scenario agent id is forwarded through `properties`, so the sidebar switches
 * scenarios the same way the custom client does.
 */
export function CopilotChatArea() {
  const selectedAgentId = useStore((s) => s.selectedAgentId);

  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      agent={COPILOT_AGENT_NAME}
      properties={{ agentId: selectedAgentId }}
    >
      <CopilotGenerativeUI />
      <div className="main">
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
        <CopilotCanvasPanel />
        <CopilotSharedStatePanel />
      </div>
    </CopilotKit>
  );
}
