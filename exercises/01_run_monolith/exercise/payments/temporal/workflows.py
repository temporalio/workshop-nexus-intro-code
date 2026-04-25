from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from compliance.domain import ComplianceRequest, ComplianceResult
    from compliance.temporal.activities import check_compliance
    from payments.domain import PaymentRequest, PaymentResult
    from payments.temporal.activities import execute_payment, validate_payment
    from shared.nexus_service import ComplianceNexusService

NEXUS_ENDPOINT = "compliance-endpoint"


@workflow.defn
class PaymentProcessingWorkflow:
    """MONOLITH VERSION - this works at Checkpoint 0.

    This workflow orchestrates 3 steps using activity stubs:
      Step 1: validate_payment   (PaymentActivity)
      Step 2: check_compliance   (ComplianceActivity) - will become Nexus
      Step 3: execute_payment    (PaymentActivity)

    TODO 4: Replace the compliance ACTIVITY call with a Nexus SERVICE call

    After completing TODOs 1-3 and creating the Nexus endpoint:

      BEFORE: compliance = await workflow.execute_activity(check_compliance, ...)
      AFTER:  nexus_client = workflow.create_nexus_client(
                  service=ComplianceNexusService, endpoint=NEXUS_ENDPOINT)
              compliance = await nexus_client.execute_operation(
                  ComplianceNexusService.check_compliance, comp_req,
                  schedule_to_close_timeout=timedelta(minutes=10))

    Same input. Same output. Different architecture.
    """

    @workflow.run
    async def process_payment(self, request: PaymentRequest) -> PaymentResult:
        try:
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

            # TODO 4: Replace this activity call with a Nexus call.
            # Delete the activity call below and create:
            #
            #   nexus_client = workflow.create_nexus_client(
            #       service=ComplianceNexusService,
            #       endpoint=NEXUS_ENDPOINT,
            #   )
            #   compliance = await nexus_client.execute_operation(
            #       ComplianceNexusService.check_compliance,
            #       comp_req,
            #       schedule_to_close_timeout=timedelta(minutes=10),
            #   )
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

        except Exception as e:
            workflow.logger.error(f"Workflow failed: {e}")
            return PaymentResult(
                success=False,
                transaction_id=request.transaction_id,
                status="FAILED",
                error=str(e),
            )
