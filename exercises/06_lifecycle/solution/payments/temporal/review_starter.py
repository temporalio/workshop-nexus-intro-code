import asyncio

from temporalio.client import Client

from compliance.domain import ComplianceResult
from payments.domain import TASK_QUEUE
from payments.temporal.workflows import ReviewCallerWorkflow
from shared.domain import ReviewRequest

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

    result: ComplianceResult = await client.execute_workflow(
        ReviewCallerWorkflow.submit_review,
        request,
        id="review-TXN-B",
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
