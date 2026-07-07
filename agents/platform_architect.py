from collections.abc import AsyncIterator

from ag_ui.core import RunAgentInput

from app.agent.base import latest_user_text
from app.agent.events import (
    AgentEvent,
    ApprovalRequested,
    DocumentDelta,
    ReasoningDelta,
    StepFinished,
    StepStarted,
    TextDelta,
    ToolCallCompleted,
    ToolCallStarted,
)
from app.agent.tools import lookup_knowledge
from app.agui.catalog import (
    APPROVAL_TOOL,
    COMMAND_OUTPUT_TOOL,
    FOLLOWUP_TOOL,
    LOOKUP_TOOL,
    TABLE_TOOL,
)
from app.agui.resume import ApprovalDecision
from agents._common import call_id, tokens


class PlatformArchitectAgent:
    """Runs cluster ops and writes Docs-as-Code for an air-gapped enterprise.

    Showcases backend_tool_rendering (live command output) plus
    predictive_state_updates (an AsciiDoc doc streamed onto the canvas).
    """

    id = "platform-architect"
    name = "Platform Architect"
    description = "Runs cluster ops and writes Docs-as-Code"
    mode = "scenario"

    async def run(self, input: RunAgentInput) -> AsyncIterator[AgentEvent]:
        target = latest_user_text(input) or "the staging EKS cluster"

        yield StepStarted("Assess")
        yield ReasoningDelta(
            "This is an air-gapped network, so public Let's Encrypt is unreachable."
        )
        yield ReasoningDelta(
            "I will provision an internal CA to issue the cluster TLS certificate."
        )
        yield StepFinished("Assess")

        for token in tokens(f'Planning changes to "{target}".'):
            yield TextDelta(token)

        lid = call_id()
        yield ToolCallStarted(
            tool_call_id=lid,
            name=LOOKUP_TOOL,
            args={"query": f"runbook for {target}"},
        )
        result = lookup_knowledge(f"runbook for {target}")
        yield ToolCallCompleted(tool_call_id=lid, result=result)

        yield StepStarted("Plan")
        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=COMMAND_OUTPUT_TOOL,
            args={
                "title": "terraform plan",
                "command": "terraform plan -out tfplan",
                "lines": [
                    {"stream": "stdout", "text": "Refreshing state..."},
                    {
                        "stream": "stdout",
                        "text": "Plan: 3 to add, 0 to change, 0 to destroy.",
                    },
                    {
                        "stream": "stdout",
                        "text": "+ tls_self_signed_cert.internal_ca (internal CA)",
                    },
                    {
                        "stream": "stdout",
                        "text": "+ aws_eks_node_group.workers (1 node group)",
                    },
                    {
                        "stream": "stdout",
                        "text": "+ kubernetes_secret.tls (cluster TLS secret)",
                    },
                ],
                "exitCode": 0,
            },
        )
        yield StepFinished("Plan")

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=TABLE_TOOL,
            args={
                "title": "Planned changes",
                "columns": ["Resource", "Action", "Count"],
                "rows": [
                    ["aws_eks_node_group", "create", "1"],
                    ["tls_self_signed_cert.internal_ca", "create", "1"],
                    ["kubernetes_secret.tls", "create", "1"],
                ],
            },
        )

        decision: ApprovalDecision = yield ApprovalRequested(
            tool_call_id=call_id(),
            name=APPROVAL_TOOL,
            args={"action": "Apply the Terraform plan", "detail": target},
        )

        if decision.approved:
            yield StepStarted("Apply")
            yield ToolCallStarted(
                tool_call_id=call_id(),
                name=COMMAND_OUTPUT_TOOL,
                args={
                    "title": "terraform apply",
                    "command": "terraform apply tfplan",
                    "lines": [
                        {"stream": "stdout", "text": "Apply complete! Resources: 3 added."},
                    ],
                    "exitCode": 0,
                },
            )
            yield StepFinished("Apply")
            for token in tokens(f'Applied the plan to "{target}".'):
                yield TextDelta(token)
        else:
            reason = decision.reason or "no reason given"
            for token in tokens(f'Did not apply the plan to "{target}" ({reason}).'):
                yield TextDelta(token)

        yield DocumentDelta(
            patch=[
                {
                    "op": "replace",
                    "path": "/document/title",
                    "value": f"= Cluster change: {target}",
                }
            ]
        )
        body = (
            "== Summary\n\n"
            f"Provisioned an EKS node group and cluster TLS for {target}.\n\n"
            "== Certificates\n\n"
            "Public Let's Encrypt is unavailable in this air-gapped network, "
            "so an internal CA issues and signs the cluster TLS certificate.\n"
        )
        yield DocumentDelta(
            patch=[{"op": "replace", "path": "/document/content", "value": body}]
        )

        yield ToolCallStarted(
            tool_call_id=call_id(),
            name=FOLLOWUP_TOOL,
            args={
                "title": "Next steps",
                "items": [
                    {
                        "label": "Rotate the internal CA",
                        "detail": "Schedule rotation before the certificate expires.",
                    },
                    {
                        "label": "Commit the AsciiDoc",
                        "detail": "Push the change record to the docs repo.",
                    },
                ],
            },
        )
