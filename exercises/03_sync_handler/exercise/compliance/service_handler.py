import nexusrpc.handler

from compliance.activities import check_compliance as _check_compliance
from compliance.models import ComplianceRequest, ComplianceResult
from shared.models import ReviewRequest
from shared.service import ComplianceNexusService

# TODO 2 (Chapter 3, Part A): add @nexusrpc.handler.service_handler(service=...)
# above the class, decorate both methods with @nexusrpc.handler.sync_operation,
# and replace each method body as shown in the README.
#
# @nexusrpc.handler.service_handler(service=ComplianceNexusService)
class ComplianceNexusServiceHandler:
    """Nexus service handler with synchronous operations.

    check_compliance: runs the rule-based checker directly and returns the result.
    submit_review: stub. Will be implemented in Ch 6 once we have a workflow to update.
    """

    # @nexusrpc.handler.sync_operation
    async def check_compliance(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ComplianceRequest
    ) -> ComplianceResult:
        # Replace with: return _check_compliance(input)
        raise NotImplementedError("TODO 2: see Chapter 3 README Part A")

    # @nexusrpc.handler.sync_operation
    async def submit_review(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
    ) -> ComplianceResult:
        # Replace with the NotImplementedError stub shown in the README.
        raise NotImplementedError("TODO 2: see Chapter 3 README Part A")
