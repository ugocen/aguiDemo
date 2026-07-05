export const LOOKUP_TOOL = "lookupKnowledge";
export const SUGGESTED_QUESTIONS_TOOL = "renderSuggestedQuestions";
export const APPROVAL_TOOL = "requestApproval";

export interface ToolSchema {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

export function toolCatalog(): ToolSchema[] {
  return [
    {
      name: SUGGESTED_QUESTIONS_TOOL,
      description: "Render a set of suggested follow-up questions as clickable chips.",
      parameters: {
        type: "object",
        properties: {
          questions: {
            type: "array",
            items: { type: "string" },
            description: "Short follow-up prompts to offer the user.",
          },
        },
        required: ["questions"],
      },
    },
    {
      name: LOOKUP_TOOL,
      description: "Look up a fact in the demo knowledge base and render the result as a card.",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string", description: "The lookup query." },
        },
        required: ["query"],
      },
    },
    {
      name: APPROVAL_TOOL,
      description: "Ask the user to approve or reject a proposed action before continuing.",
      parameters: {
        type: "object",
        properties: {
          action: { type: "string", description: "The action awaiting approval." },
          detail: { type: "string", description: "Context for the decision." },
        },
        required: ["action"],
      },
    },
  ];
}
