import nexusrpc.handler

from compliance.activities import check_compliance as _check_compliance
from compliance.models import ComplianceRequest, ComplianceResult
from shared.models import ReviewRequest
from shared.service import ComplianceNexusService

@nexusrpc.handler.service_handler(service=ComplianceNexusService)
class ComplianceNexusServiceHandler:
    """Nexus service handler with synchronous operations.

    check_compliance runs the rule-based checker directly and returns the result.
    submit_review is a stub; it gains a real implementation later in the workshop.
    """

    @nexusrpc.handler.sync_operation
    async def check_compliance(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ComplianceRequest
    ) -> ComplianceResult:
        # Sync handlers can run arbitrary code within the 10-second deadline.
        # We call the rule-based check_compliance function directly. The @activity.defn
        # decorator on it doesn't change call semantics - it just registers metadata
        # for workers; calling it as a plain function bypasses the activity machinery.
        return _check_compliance(input)

    @nexusrpc.handler.sync_operation
    async def submit_review(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
    ) -> ComplianceResult:
        # Later in the workshop this will use the Temporal Client to send a
        # Workflow Update to the running ComplianceWorkflow. For now this path
        # is unreachable because no caller invokes submit_review yet.
        raise NotImplementedError(
            "submit_review is a stub; it gains a real implementation later in the workshop"
        )
