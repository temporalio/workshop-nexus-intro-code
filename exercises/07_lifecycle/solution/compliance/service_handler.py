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
    """Nexus service handler with lifecycle-failure injection.

    For Ch 7 lifecycle exercises, check_compliance recognizes special transaction_id
    prefixes and raises Nexus errors before starting the workflow:

      - TXN-FAIL-NONRETRY: raises nexusrpc.OperationError (non-retryable, FAILED state).
        The caller records NexusOperationFailed immediately.
      - TXN-FAIL-RETRY:    raises nexusrpc.HandlerError(INTERNAL).
        The Nexus machinery treats this as retryable and backs off.
      - TXN-CIRCUIT:       raises nexusrpc.HandlerError(INTERNAL) for every call.
        Sending several of these in succession trips the circuit breaker.

    Normal transactions go through to ComplianceWorkflow as in Ch 5.
    """

    @nexus.workflow_run_operation
    async def check_compliance(
        self, ctx: nexus.WorkflowRunOperationContext, input: ComplianceRequest
    ) -> nexus.WorkflowHandle[ComplianceResult]:
        txn_id = input.transaction_id

        # Lifecycle scenarios for Ch 7: inject failures by transaction_id prefix.
        if txn_id.startswith("TXN-FAIL-NONRETRY"):
            raise nexusrpc.OperationError(
                "Permanent compliance failure (non-retryable)",
                state=nexusrpc.OperationErrorState.FAILED,
            )
        if txn_id.startswith("TXN-FAIL-RETRY") or txn_id.startswith("TXN-CIRCUIT"):
            raise nexusrpc.HandlerError(
                "Transient compliance failure (retryable)",
                type=nexusrpc.HandlerErrorType.INTERNAL,
            )

        # The workflow ID is business-meaningful so it is easy to find in the UI.
        # USE_EXISTING makes the handler idempotent: a retried Nexus start request
        # for the same transaction returns a handle to the already-running workflow
        # instead of failing with WorkflowAlreadyStartedError.
        return await ctx.start_workflow(
            ComplianceWorkflow.run,
            input,
            id=f"compliance-{txn_id}",
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
