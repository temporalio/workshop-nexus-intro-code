from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    # TODO 4a: After TODO 4b, this import is no longer used. Remove it.
    from compliance.activities import check_compliance
    from compliance.models import ComplianceRequest, ComplianceResult
    from payments.activities import execute_payment, validate_payment
    from payments.models import PaymentRequest, PaymentResult
    from shared.service import ComplianceNexusService

NEXUS_ENDPOINT = "compliance-endpoint"

@workflow.defn
class PaymentProcessingWorkflow:
    """Starting point for Ch 4: compliance check is still a local activity.

    Step 1: validate_payment   (Payments team)
    Step 2: check_compliance   (Compliance team) - will become Nexus in TODO 4b
    Step 3: execute_payment    (Payments team)

    Error model: activity, child-workflow, and Nexus operation failures are allowed
    to propagate so the Workflow Execution itself ends in the Failed state, and
    cancellation propagates so the Execution ends as Canceled. Application-level
    "this transaction will not go through" outcomes (REJECTED, DECLINED_COMPLIANCE)
    are returned as PaymentResult so callers can inspect them on a successful run.
    """

    @workflow.run
    async def process_payment(self, request: PaymentRequest) -> PaymentResult:
        # Step 1: Validate payment (Payments team)
        valid = await workflow.execute_activity(
            validate_payment,
            request,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                backoff_coefficient=2,
            ),
        )
        if not valid:
            return PaymentResult(
                success=False,
                transaction_id=request.transaction_id,
                status="REJECTED",
                error="Payment validation failed",
            )
        workflow.logger.info(f"Step 1 passed: validation OK for {request.transaction_id}")

        # Step 2: Compliance check
        comp_req = ComplianceRequest(
            transaction_id=request.transaction_id,
            amount=request.amount,
            sender_country=request.sender_country,
            receiver_country=request.receiver_country,
            description=request.description,
        )

        workflow.logger.info(
            f"Step 2: calling compliance check for {request.transaction_id}"
        )

        # TODO 4b: Replace this activity call with a Nexus call. See the README for the full code.
        compliance: ComplianceResult = await workflow.execute_activity(
            check_compliance,
            comp_req,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                backoff_coefficient=2,
            ),
        )

        workflow.logger.info(
            f"Compliance result: {compliance.risk_level} | approved={compliance.approved}"
        )

        if not compliance.approved:
            return PaymentResult(
                success=False,
                transaction_id=request.transaction_id,
                status="DECLINED_COMPLIANCE",
                risk_level=compliance.risk_level,
                explanation=compliance.explanation,
            )

        # Step 3: Execute payment (only if compliance approved)
        workflow.logger.info(f"Step 3: executing payment for {request.transaction_id}")
        confirmation = await workflow.execute_activity(
            execute_payment,
            request,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                backoff_coefficient=2,
            ),
        )

        return PaymentResult(
            success=True,
            transaction_id=request.transaction_id,
            status="COMPLETED",
            risk_level=compliance.risk_level,
            explanation=compliance.explanation,
            confirmation_number=confirmation,
        )
