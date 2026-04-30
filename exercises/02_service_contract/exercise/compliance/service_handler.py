import nexusrpc.handler

from compliance.activities import check_compliance as _check_compliance
from compliance.models import ComplianceRequest, ComplianceResult
from shared.models import ReviewRequest
from shared.service import ComplianceNexusService

# TODO 2a (Chapter 3): Add the @nexusrpc.handler.service_handler decorator (bound to ComplianceNexusService) on the line below.
class ComplianceNexusServiceHandler:
    """Nexus service handler with synchronous operations.

    check_compliance: runs the rule-based checker directly and returns the result.
    submit_review: stub. Will be implemented in Ch 6 once we have a workflow to update.
    """

    # TODO 2b (Chapter 3): Decorate the method below with @nexusrpc.handler.sync_operation, then implement the body.
    async def check_compliance(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ComplianceRequest
    ) -> ComplianceResult:
        pass

    # TODO 2c (Chapter 3): Decorate the method below with @nexusrpc.handler.sync_operation, then implement the body.
    async def submit_review(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
    ) -> ComplianceResult:
        pass
