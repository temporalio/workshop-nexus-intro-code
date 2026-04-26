from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from compliance.activities import check_compliance
    from compliance.models import ComplianceRequest, ComplianceResult

@workflow.defn
class ComplianceWorkflow:
    """Runs automated compliance check; for MEDIUM risk waits on human review.

    LOW risk  -> auto-approved, returns immediately
    HIGH risk -> auto-denied, returns immediately
    MEDIUM    -> pauses, waits for review() Update
    """

    def __init__(self) -> None:
        self._request: ComplianceRequest | None = None
        self._auto_result: ComplianceResult | None = None
        # TODO 10 (Chapter 6, Part A): Add the @workflow.update review path with validator.

    @workflow.run
    async def run(self, request: ComplianceRequest) -> ComplianceResult:
        self._request = request
        self._auto_result = await workflow.execute_activity(
            check_compliance,
            request,
            start_to_close_timeout=timedelta(seconds=30),
        )
        return self._auto_result

