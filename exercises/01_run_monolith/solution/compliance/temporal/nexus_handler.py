# ===================================================================
#  TODO 2: Implement the synchronous Nexus service handlers
# ===================================================================
#
# This class implements the ComplianceNexusService interface.
# Both operations are SYNCHRONOUS in this chapter - sync handlers must
# complete within the 10-second handler deadline.
#
#   1. Add @nexusrpc.handler.service_handler(service=ComplianceNexusService) to the class
#   2. Implement check_compliance: call ComplianceChecker directly and return the result
#   3. Stub submit_review with NotImplementedError
#
# check_compliance - sync handler that classifies the transaction
#
#   @nexusrpc.handler.sync_operation
#   async def check_compliance(
#       self, ctx: nexusrpc.handler.StartOperationContext, input: ComplianceRequest
#   ) -> ComplianceResult:
#       return _check_compliance(input)
#
# submit_review - stub (will be implemented in Ch 5)
#
# submit_review needs a target workflow to send an Update to. The
# ComplianceWorkflow (and the workflow-backed check_compliance handler)
# is introduced in Ch 5. For now, raise NotImplementedError so the
# worker starts, but the operation is unreachable.
#
#   @nexusrpc.handler.sync_operation
#   async def submit_review(
#       self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
#   ) -> ComplianceResult:
#       raise NotImplementedError(
#           "submit_review requires the workflow-backed check, see Ch 5"
#       )

import nexusrpc.handler

from compliance.compliance_checker import check_compliance as _check_compliance
from compliance.domain import ComplianceRequest, ComplianceResult
from shared.domain import ReviewRequest
from shared.nexus_service import ComplianceNexusService


# TODO 2: Add @nexusrpc.handler.service_handler(service=ComplianceNexusService) decorator
class ComplianceNexusServiceHandler:
    """Nexus service handler with synchronous operations.

    check_compliance: runs the rule-based checker directly and returns the result.
    submit_review: stub. Will be implemented in Ch 5 once we have a workflow to update.
    """

    # TODO 2: Add @nexusrpc.handler.sync_operation decorator and implement check_compliance
    async def check_compliance(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ComplianceRequest
    ) -> ComplianceResult:
        return None

    # TODO 2: Add @nexusrpc.handler.sync_operation decorator and stub submit_review
    async def submit_review(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
    ) -> ComplianceResult:
        return None
