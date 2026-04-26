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
        # TODO 6 (Chapter 5, Part A): Implement ComplianceWorkflow.run (run the activity, return the result).
        raise NotImplementedError("TODO 6: see the chapter README")
