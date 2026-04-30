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

    Ch 5: check_compliance is workflow-backed (async); submit_review is still a stub.
    Ch 6: submit_review becomes a real sync handler that sends a Workflow Update.
    """

    @nexus.workflow_run_operation
    async def check_compliance(
        self, ctx: nexus.WorkflowRunOperationContext, input: ComplianceRequest
    ) -> nexus.WorkflowHandle[ComplianceResult]:
        # The workflow ID is business-meaningful so it is easy to find in the UI.
        # USE_EXISTING makes the handler idempotent: a retried Nexus start request
        # for the same transaction returns a handle to the already-running workflow
        # instead of failing with WorkflowAlreadyStartedError.
        return await ctx.start_workflow(
            ComplianceWorkflow.run,
            input,
            id=f"compliance-ch05-{input.transaction_id}",
            id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
        )

    @nexusrpc.handler.sync_operation
    async def submit_review(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
    ) -> ComplianceResult:
        # Ch 6 turns this into a real Update sender once ComplianceWorkflow has a
        # @workflow.update review handler. For now no caller invokes submit_review,
        # so this raise is unreachable.
        raise NotImplementedError(
            "submit_review is implemented in Ch 6 once ComplianceWorkflow has a review Update"
        )
