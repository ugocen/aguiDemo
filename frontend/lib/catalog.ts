export const LOOKUP_TOOL = "lookupKnowledge";
export const SUGGESTED_QUESTIONS_TOOL = "renderSuggestedQuestions";
export const APPROVAL_TOOL = "requestApproval";
export const TABLE_TOOL = "renderTable";
export const FOLLOWUP_TOOL = "renderFollowUp";
export const CHART_TOOL = "renderChart";
export const CITATIONS_TOOL = "renderCitations";
export const FORM_TOOL = "renderForm";

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
    {
      name: TABLE_TOOL,
      description: "Render structured tabular data as a table card.",
      parameters: {
        type: "object",
        properties: {
          title: { type: "string", description: "Table caption." },
          columns: { type: "array", items: { type: "string" }, description: "Column headers." },
          rows: {
            type: "array",
            items: { type: "array", items: { type: "string" } },
            description: "Row values, aligned to columns.",
          },
        },
        required: ["columns", "rows"],
      },
    },
    {
      name: FOLLOWUP_TOOL,
      description: "Render follow-up information or next steps as a list card.",
      parameters: {
        type: "object",
        properties: {
          title: { type: "string", description: "Section heading." },
          items: {
            type: "array",
            items: {
              type: "object",
              properties: { label: { type: "string" }, detail: { type: "string" } },
              required: ["label"],
            },
            description: "Follow-up entries.",
          },
        },
        required: ["items"],
      },
    },
    {
      name: CHART_TOOL,
      description: "Render a simple bar chart from labeled numeric series.",
      parameters: {
        type: "object",
        properties: {
          title: { type: "string", description: "Chart caption." },
          unit: { type: "string", description: "Optional value unit, e.g. %." },
          series: {
            type: "array",
            items: {
              type: "object",
              properties: { label: { type: "string" }, value: { type: "number" } },
              required: ["label", "value"],
            },
            description: "Bars to plot.",
          },
        },
        required: ["series"],
      },
    },
    {
      name: CITATIONS_TOOL,
      description: "Render a list of sources with titles, links, and snippets.",
      parameters: {
        type: "object",
        properties: {
          title: { type: "string", description: "Section heading." },
          sources: {
            type: "array",
            items: {
              type: "object",
              properties: {
                title: { type: "string" },
                url: { type: "string" },
                snippet: { type: "string" },
              },
              required: ["title"],
            },
            description: "Cited sources.",
          },
        },
        required: ["sources"],
      },
    },
    {
      name: FORM_TOOL,
      description: "Ask the user for structured input by rendering a form.",
      parameters: {
        type: "object",
        properties: {
          title: { type: "string", description: "Form heading." },
          submitLabel: { type: "string", description: "Submit button text." },
          fields: {
            type: "array",
            items: {
              type: "object",
              properties: {
                name: { type: "string" },
                label: { type: "string" },
                type: { type: "string", description: "text, email, or number." },
                placeholder: { type: "string" },
              },
              required: ["name", "label"],
            },
            description: "Fields to collect.",
          },
        },
        required: ["fields"],
      },
    },
  ];
}
