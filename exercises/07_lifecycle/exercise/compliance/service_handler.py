# TODO 13a: Add `import nexusrpc` directly above the `import nexusrpc.handler` line below.
# The branches you add in TODO 13b raise nexusrpc.OperationError and nexusrpc.HandlerError,
# so the top-level package must be in scope.
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
        # TODO 13b: Add three failure-injection branches before start_workflow.
        # Match transaction-id prefixes (TXN-FAIL-NONRETRY, TXN-FAIL-RETRY, TXN-CIRCUIT)
        # and raise the matching nexusrpc.OperationError or nexusrpc.HandlerError.
        # See the README for the full code.

        # USE_EXISTING makes the handler idempotent on retry: a retried Nexus
        # start request for the same transaction returns a handle to the
        # already-running workflow instead of failing with WorkflowAlreadyStartedError.
        return await ctx.start_workflow(
            ComplianceWorkflow.run,
            input,
            id=f"compliance-ch07-{input.transaction_id}",
            id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
        )

    @nexusrpc.handler.sync_operation
    async def submit_review(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
    ) -> ComplianceResult:
        client = nexus.client()
        handle: WorkflowHandle = client.get_workflow_handle_for(
            ComplianceWorkflow.run,
            workflow_id=f"compliance-ch07-{input.transaction_id}",
        )
        return await handle.execute_update(
            ComplianceWorkflow.review,
            args=[input.approved, input.explanation],
        )
