import nexusrpc.handler

from compliance.compliance_checker import check_compliance as _check_compliance
from compliance.domain import ComplianceRequest, ComplianceResult
from shared.domain import ReviewRequest
from shared.nexus_service import ComplianceNexusService


@nexusrpc.handler.service_handler(service=ComplianceNexusService)
class ComplianceNexusServiceHandler:
    """Nexus service handler with synchronous operations.

    check_compliance runs the rule-based checker directly and returns the result.
    submit_review is a stub. It will be implemented in Ch 5 once we have a workflow to update.
    """

    @nexusrpc.handler.sync_operation
    async def check_compliance(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ComplianceRequest
    ) -> ComplianceResult:
        # Sync handlers can run arbitrary code within the 10-second deadline.
        # We delegate to the rule-based ComplianceChecker.
        return _check_compliance(input)

    @nexusrpc.handler.sync_operation
    async def submit_review(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
    ) -> ComplianceResult:
        # In Ch 5, this will use the Temporal Client to send a Workflow Update
        # to the running ComplianceWorkflow. For now this path is unreachable
        # because no caller invokes submit_review yet.
        raise NotImplementedError(
            "submit_review requires the workflow-backed compliance check, introduced in Ch 5"
        )
