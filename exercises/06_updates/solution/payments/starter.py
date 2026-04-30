import asyncio

from temporalio.client import Client

from payments.models import TASK_QUEUE, PaymentRequest, PaymentResult
from payments.workflows import PaymentProcessingWorkflow

NAMESPACE = "payments-namespace"

async def main() -> None:
    print("==========================================================")
    print("  PAYMENT STARTER")
    print("  Running 3 transactions through Temporal")
    print("==========================================================\n")

    client = await Client.connect("localhost:7233", namespace=NAMESPACE)

    transactions = [
        PaymentRequest(
            "TXN-A", 250.00, "USD", "US", "US",
            "Routine supplier payment", "ACC-001", "ACC-002",
        ),
        PaymentRequest(
            "TXN-B", 12000.00, "USD", "US", "UK",
            "International consulting fee", "ACC-003", "ACC-004",
        ),
        PaymentRequest(
            "TXN-C", 75000.00, "USD", "US", "US",
            "Large capital transfer", "ACC-005", "ACC-006",
        ),
    ]

    for txn in transactions:
        workflow_id = f"payment-ch06-{txn.transaction_id}"

        print("--------------------------------------------------")
        print(f"  Starting: {workflow_id}")
        print(f"  Amount: ${txn.amount:.2f} | Route: {txn.sender_country} -> {txn.receiver_country}")
        print("--------------------------------------------------")

        result: PaymentResult = await client.execute_workflow(
            PaymentProcessingWorkflow.process_payment,
            txn,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )

        print(f"\n  Result: {result.status}")
        print(f"  Risk:   {result.risk_level or 'N/A'}")
        print(f"  Reason: {result.explanation or 'N/A'}")
        if result.confirmation_number:
            print(f"  Conf#:  {result.confirmation_number}")
        if result.error:
            print(f"  Error:  {result.error}")
        print()

    print("==========================================================")
    print("  All 3 transactions processed!")
    print("  Check Temporal UI: http://localhost:8233")
    print("==========================================================")

if __name__ == "__main__":
    asyncio.run(main())
