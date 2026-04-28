import asyncio
import uuid

from temporalio.client import Client

from compliance.models import ComplianceResult
from payments.models import TASK_QUEUE
from payments.workflows import ReviewCallerWorkflow
from shared.models import ReviewRequest

NAMESPACE = "payments-namespace"

async def main() -> None:
    print("==========================================================")
    print("  REVIEW STARTER - Submitting review for TXN-B via Nexus")
    print("==========================================================\n")

    client = await Client.connect("localhost:7233", namespace=NAMESPACE)

    # Change approved to False to deny instead
    request = ReviewRequest(
        transaction_id="TXN-B",
        approved=True,
        explanation="Approved after manual review",
    )

    print("  Submitting review for TXN-B via Nexus...")
    print(f"  Approved: {request.approved}")
    print(f"  Explanation: {request.explanation}")
    print()

    # The ReviewCallerWorkflow is short-lived - one Nexus call, then done. We
    # tag its ID with a fresh UUID so attendees can re-run this starter without
    # hitting WorkflowAlreadyStartedError. The Update it sends targets the
    # long-running compliance-ch07-{transaction_id} workflow, which has the stable
    # business ID.
    workflow_id = f"review-TXN-B-{uuid.uuid4()}"
    result: ComplianceResult = await client.execute_workflow(
        ReviewCallerWorkflow.submit_review,
        request,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    approved_str = "APPROVED" if result.approved else "DENIED"
    print(f"  Review result: {approved_str}")
    print(f"  Risk level:    {result.risk_level}")
    print(f"  Explanation:   {result.explanation}")
    print()
    print("  TXN-B review submitted! The payment workflow will now complete.")
    print("==========================================================")

if __name__ == "__main__":
    asyncio.run(main())
