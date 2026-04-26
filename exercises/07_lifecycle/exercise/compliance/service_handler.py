import nexusrpc
import nexusrpc.handler
from temporalio import nexus
from temporalio.client import WorkflowHandle
from temporalio.common import WorkflowIDConflictPolicy

from compliance.models import ComplianceRequest, ComplianceResult
from compliance.workflows import ComplianceWorkflow
from shared.models import ReviewRequest
from shared.service import ComplianceNexusService

@nexusrpc.handler.service_handler(service=ComplianceNexusService)
class ComplianceNexusServiceHandler:
    """Nexus service handler.

    For Chapter 7, check_compliance recognizes special transaction_id prefixes
    (TXN-FAIL-NONRETRY, TXN-FAIL-RETRY, TXN-CIRCUIT) and raises Nexus errors
    before starting the workflow.
    """

    @nexus.workflow_run_operation
    async def check_compliance(
        self, ctx: nexus.WorkflowRunOperationContext, input: ComplianceRequest
    ) -> nexus.WorkflowHandle[ComplianceResult]:
        # TODO 13 (Chapter 7, Part A): Add the failure-injection branches before start_workflow.

        # USE_EXISTING makes the handler idempotent on retry: a retried Nexus
        # start request for the same transaction returns a handle to the
        # already-running workflow instead of failing with WorkflowAlreadyStartedError.
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
        client = nexus.client()
        handle: WorkflowHandle = client.get_workflow_handle_for(
            ComplianceWorkflow.run,
            workflow_id=f"compliance-{input.transaction_id}",
        )
        return await handle.execute_update(
            ComplianceWorkflow.review,
            args=[input.approved, input.explanation],
        )
