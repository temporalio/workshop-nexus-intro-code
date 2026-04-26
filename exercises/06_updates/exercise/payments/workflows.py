from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from compliance.models import ComplianceRequest, ComplianceResult
    from payments.activities import execute_payment, validate_payment
    from payments.models import PaymentRequest, PaymentResult
    from shared.service import ComplianceNexusService

NEXUS_ENDPOINT = "compliance-endpoint"

@workflow.defn
class PaymentProcessingWorkflow:
    """ASYNC NEXUS VERSION.

    The compliance check is now an asynchronous Nexus operation backed by a workflow
    on the Compliance side. In Ch 5 the workflow simply runs the rule-based check and
    returns; MEDIUM-risk transactions auto-approve with the AML monitoring note. The
    human-in-the-loop review path arrives in Ch 6.

    Three timeouts are configured on the Nexus call:
      - schedule_to_close_timeout: total budget from when we schedule the operation
        until it must complete. Bounds the worst case across retries.
      - schedule_to_start_timeout: how long we'll wait for the handler to pick up
        the operation. Trips early if the Compliance worker is unhealthy.
      - start_to_close_timeout: once the handler has started, the caller-side cap on
        how long the operation may run before being treated as timed out.

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

        # Step 2: Compliance check via Nexus (Compliance team)
        comp_req = ComplianceRequest(
            transaction_id=request.transaction_id,
            amount=request.amount,
            sender_country=request.sender_country,
            receiver_country=request.receiver_country,
            description=request.description,
        )

        workflow.logger.info(
            f"Step 2: calling compliance check via Nexus for {request.transaction_id}"
        )

        nexus_client = workflow.create_nexus_client(
            service=ComplianceNexusService,
            endpoint=NEXUS_ENDPOINT,
        )
        compliance: ComplianceResult = await nexus_client.execute_operation(
            ComplianceNexusService.check_compliance,
            comp_req,
            schedule_to_close_timeout=timedelta(minutes=10),
            schedule_to_start_timeout=timedelta(minutes=1),
            start_to_close_timeout=timedelta(minutes=8),
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


# TODO 12 (Chapter 6, Part C): Add a `ReviewCallerWorkflow` class below, and add
# `from shared.models import ReviewRequest` to the `imports_passed_through` block above.
