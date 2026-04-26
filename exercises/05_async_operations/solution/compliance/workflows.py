from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from compliance.activities import check_compliance
    from compliance.models import ComplianceRequest, ComplianceResult

@workflow.defn
class ComplianceWorkflow:
    """Runs the automated, rule-based compliance check.

    Ch 5: classifies the transaction and returns the result. LOW, MEDIUM,
    and HIGH all return whatever the rule-based check produces.

    Ch 6 will add a human-review path for MEDIUM-risk transactions.
    """

    def __init__(self) -> None:
        self._request: ComplianceRequest | None = None
        self._auto_result: ComplianceResult | None = None

    @workflow.run
    async def run(self, request: ComplianceRequest) -> ComplianceResult:
        self._request = request
        # Run the rule-based check as an activity. Storing the result on
        # self._auto_result (rather than a local) lets Ch 6 extend this
        # method to wait for a human review on the MEDIUM branch without
        # restructuring the part written here.
        self._auto_result = await workflow.execute_activity(
            check_compliance,
            request,
            start_to_close_timeout=timedelta(seconds=30),
        )
        return self._auto_result
