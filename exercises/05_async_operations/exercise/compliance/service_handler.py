import nexusrpc.handler
from temporalio import nexus
from temporalio.common import WorkflowIDConflictPolicy

# TODO 7b: After converting check_compliance to async, this import is no longer used. Remove it.
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

    # TODO 7a: Convert this sync handler to a workflow-backed async handler.
    # Replace the decorator, context type, return type, and body so that this
    # handler starts a ComplianceWorkflow and returns its handle.
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
