import nexusrpc.handler
from temporalio import nexus
from temporalio.common import WorkflowIDConflictPolicy

from compliance.models import ComplianceRequest, ComplianceResult
from compliance.workflows import ComplianceWorkflow
from shared.models import ReviewRequest
from shared.service import ComplianceNexusService

@nexusrpc.handler.service_handler(service=ComplianceNexusService)
class ComplianceNexusServiceHandler:
    """Nexus service handler.

    check_compliance: async (workflow_run_operation) - starts a new ComplianceWorkflow.
    submit_review: sync (sync_operation) - sends a Workflow Update to the running workflow.
    """

    @nexus.workflow_run_operation
    async def check_compliance(
        self, ctx: nexus.WorkflowRunOperationContext, input: ComplianceRequest
    ) -> nexus.WorkflowHandle[ComplianceResult]:
        return await ctx.start_workflow(
            ComplianceWorkflow.run,
            input,
            id=f"compliance-{input.transaction_id}",
            id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
        )

    @nexusrpc.handler.sync_operation
    async def submit_review(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
    ) -> ComplianceResult:
        # TODO 11 (Chapter 6, Part B): Replace the NotImplementedError stub with a real Update sender.
        raise NotImplementedError(
            "submit_review: see Chapter 6 README Part B"
        )
