import nexusrpc.handler
from temporalio import nexus
from temporalio.common import WorkflowIDConflictPolicy

from compliance.activities import check_compliance as _check_compliance
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

    # TODO 7 (Chapter 5, Part B): Convert check_compliance to @nexus.workflow_run_operation.
    @nexusrpc.handler.sync_operation
    async def check_compliance(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ComplianceRequest
    ) -> ComplianceResult:
        return _check_compliance(input)

    @nexusrpc.handler.sync_operation
    async def submit_review(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
    ) -> ComplianceResult:
        raise NotImplementedError(
            "submit_review is implemented in Ch 6 once ComplianceWorkflow has a review Update"
        )
