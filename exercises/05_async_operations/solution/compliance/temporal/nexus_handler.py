import nexusrpc.handler
from temporalio import nexus
from temporalio.client import WorkflowHandle

from compliance.domain import ComplianceRequest, ComplianceResult
from compliance.temporal.workflows import ComplianceWorkflow
from shared.domain import ReviewRequest
from shared.nexus_service import ComplianceNexusService


@nexusrpc.handler.service_handler(service=ComplianceNexusService)
class ComplianceNexusServiceHandler:
    """Nexus service handler - receives cross-team calls from Payments.

    Two handlers:
      - check_compliance: async (workflow_run_operation) - starts a new ComplianceWorkflow
      - submit_review: sync (sync_operation) - sends Update to a running workflow
    """

    @nexus.workflow_run_operation
    async def check_compliance(
        self, ctx: nexus.WorkflowRunOperationContext, input: ComplianceRequest
    ) -> nexus.WorkflowHandle[ComplianceResult]:
        return await ctx.start_workflow(
            ComplianceWorkflow.run,
            input,
            id=f"compliance-{input.transaction_id}",
        )

    @nexusrpc.handler.sync_operation
    async def submit_review(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
    ) -> ComplianceResult:
        client = nexus.client()
        handle: WorkflowHandle = client.get_workflow_handle_for(
            ComplianceWorkflow.run,
            workflow_id=f"compliance-{input.transaction_id}",
        )
        return await handle.execute_update(
            ComplianceWorkflow.review,
            args=[input.approved, input.explanation],
        )
