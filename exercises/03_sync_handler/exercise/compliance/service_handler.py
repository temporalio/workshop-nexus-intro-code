import nexusrpc.handler

from compliance.activities import check_compliance as _check_compliance
from compliance.models import ComplianceRequest, ComplianceResult
from shared.models import ReviewRequest
from shared.service import ComplianceNexusService

# TODO 2a: Bind this class to the ComplianceNexusService contract so it counts as a service handler.
class ComplianceNexusServiceHandler:
    """Nexus service handler with synchronous operations.

    check_compliance: runs the rule-based checker directly and returns the result.
    submit_review: stub. Gains a real implementation later in the workshop.
    """

    # TODO 2b: Mark this method as a synchronous Nexus operation handler and return the rule-based check result.
    async def check_compliance(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ComplianceRequest
    ) -> ComplianceResult:
        pass

    # TODO 2c: Mark this method as a synchronous Nexus operation handler and stub it out (real implementation comes later in the workshop).
    async def submit_review(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
    ) -> ComplianceResult:
        pass
