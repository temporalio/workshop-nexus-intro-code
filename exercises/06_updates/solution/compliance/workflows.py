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

    @workflow.init
    def __init__(self, request: ComplianceRequest) -> None:
        self._request: ComplianceRequest = request
        self._auto_result: ComplianceResult | None = None
        self._review_result: ComplianceResult | None = None

    @workflow.run
    async def run(self, request: ComplianceRequest) -> ComplianceResult:

        # Step 1: Run automated compliance check
        self._auto_result = await workflow.execute_activity(
            check_compliance,
            request,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 2: LOW or HIGH risk -> return immediately
        if self._auto_result.risk_level != "MEDIUM":
            return self._auto_result

        # Step 3: MEDIUM risk -> sleep then wait for human review via Update.
        # The sleep demonstrates Nexus + Temporal durability: kill the compliance
        # worker mid-sleep, restart it, and the workflow resumes from where it
        # left off. The wait_condition below is also durable, so cancellation and
        # reviewer Updates flow through correctly even across worker restarts.
        await workflow.sleep(timedelta(seconds=10))
        await workflow.wait_condition(lambda: self._review_result is not None)
        return self._review_result

    @workflow.update
    async def review(self, approved: bool, explanation: str) -> ComplianceResult:
        self._review_result = ComplianceResult(
            transaction_id=self._request.transaction_id,
            approved=approved,
            risk_level="MEDIUM",
            explanation=explanation,
        )
        return self._review_result

    @review.validator
    def validate_review(self, approved: bool, explanation: str) -> None:
        if self._auto_result is None or self._auto_result.risk_level != "MEDIUM":
            raise ValueError("Workflow is not awaiting review")
        if self._review_result is not None:
            raise ValueError("Review already submitted")
