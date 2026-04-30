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
        # TODO 10a: Add a third instance variable, _review_result, for the human-reviewer outcome.

    @workflow.run
    async def run(self, request: ComplianceRequest) -> ComplianceResult:
        self._auto_result = await workflow.execute_activity(
            check_compliance,
            request,
            start_to_close_timeout=timedelta(seconds=30),
        )
        # TODO 10b: Branch on the auto-check's risk level. LOW and HIGH should return
        # the automated result immediately; MEDIUM should pause until a human review
        # arrives, then return that reviewer's outcome. See the README for the body.
        pass

    # TODO 10c: Below this line, add the human-review Update entry point and its
    # validator so reviewers can submit a decision into a paused MEDIUM workflow.
    # See the README for the full code.
