# ===================================================================
#  TODO 11: Inject lifecycle failures into check_compliance
# ===================================================================
#
# Ch 6 demonstrates Nexus lifecycle behaviors: cancellation, retryable vs
# non-retryable errors, and the circuit breaker. The lifecycle_starter.py
# script exercises each scenario by sending transactions with special
# transaction_id prefixes. Your job is to recognize those prefixes in the
# handler and raise the appropriate Nexus error before starting the workflow.
#
# Add three branches at the top of check_compliance, before the start_workflow call:
#
#   1. TXN-FAIL-NONRETRY*  - raise nexusrpc.OperationError with state FAILED
#                            (non-retryable: caller records NexusOperationFailed)
#
#   2. TXN-FAIL-RETRY*     - raise nexusrpc.HandlerError with type INTERNAL
#                            (retryable: caller's Pending Operations show BackingOff)
#
#   3. TXN-CIRCUIT*        - raise nexusrpc.HandlerError with type INTERNAL
#                            (same as above, but lifecycle_starter sends 6+ in
#                            succession to trip the circuit breaker)
#
# Pattern:
#
#   txn_id = input.transaction_id
#
#   if txn_id.startswith("TXN-FAIL-NONRETRY"):
#       raise nexusrpc.OperationError(
#           "Permanent compliance failure (non-retryable)",
#           state=nexusrpc.OperationErrorState.FAILED,
#       )
#   if txn_id.startswith("TXN-FAIL-RETRY") or txn_id.startswith("TXN-CIRCUIT"):
#       raise nexusrpc.HandlerError(
#           "Transient compliance failure (retryable)",
#           type=nexusrpc.HandlerErrorType.INTERNAL,
#       )
#
# Cancellation (Scenario C in lifecycle_starter) does not require handler changes.
# Cancellation propagates from a cancelled caller workflow through the running
# Nexus operation to the underlying ComplianceWorkflow automatically.

import nexusrpc
import nexusrpc.handler
from temporalio import nexus
from temporalio.client import WorkflowHandle

from compliance.domain import ComplianceRequest, ComplianceResult
from compliance.temporal.workflows import ComplianceWorkflow
from shared.domain import ReviewRequest
from shared.nexus_service import ComplianceNexusService


@nexusrpc.handler.service_handler(service=ComplianceNexusService)
class ComplianceNexusServiceHandler:
    """Nexus service handler.

    For Ch 6, check_compliance recognizes special transaction_id prefixes
    (TXN-FAIL-NONRETRY, TXN-FAIL-RETRY, TXN-CIRCUIT) and raises Nexus errors
    before starting the workflow. See TODO 11.
    """

    @nexus.workflow_run_operation
    async def check_compliance(
        self, ctx: nexus.WorkflowRunOperationContext, input: ComplianceRequest
    ) -> nexus.WorkflowHandle[ComplianceResult]:
        # TODO 11: Add the three lifecycle-failure branches here.
        # See the docstring at the top of this file for the exact code.

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
