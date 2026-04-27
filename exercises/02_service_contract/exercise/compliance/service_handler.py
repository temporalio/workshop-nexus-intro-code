import nexusrpc.handler

from compliance.activities import check_compliance as _check_compliance
from compliance.models import ComplianceRequest, ComplianceResult
from shared.models import ReviewRequest
from shared.service import ComplianceNexusService

# TODO 2 (Chapter 3, Part A): Implement the sync Nexus handlers.
class ComplianceNexusServiceHandler:
    """Nexus service handler with synchronous operations.

    check_compliance: runs the rule-based checker directly and returns the result.
    submit_review: stub. Will be implemented in Ch 6 once ComplianceWorkflow has a review Update.
    """

    async def check_compliance(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ComplianceRequest
    ) -> ComplianceResult:
        raise NotImplementedError("TODO 2: see Chapter 3 README Part A")

    async def submit_review(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
    ) -> ComplianceResult:
        raise NotImplementedError("TODO 2: see Chapter 3 README Part A")
