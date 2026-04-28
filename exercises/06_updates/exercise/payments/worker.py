import asyncio
import concurrent.futures

from temporalio.client import Client
from temporalio.worker import Worker

from payments.activities import execute_payment, validate_payment
from payments.models import TASK_QUEUE
# TODO 12c: Update this import to also bring in ReviewCallerWorkflow.
from payments.workflows import PaymentProcessingWorkflow

NAMESPACE = "payments-namespace"

async def main() -> None:
    """Payments worker - hosts PaymentProcessingWorkflow and (Ch 6) ReviewCallerWorkflow."""
    client = await Client.connect("localhost:7233", namespace=NAMESPACE)

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        worker = Worker(
            client,
            task_queue=TASK_QUEUE,
            # TODO 12d: Add ReviewCallerWorkflow to this list so the Worker registers it.
            workflows=[PaymentProcessingWorkflow],
            activities=[validate_payment, execute_payment],
            activity_executor=executor,
        )
        print("=========================================================")
        print(f"  Payments Worker started on: {TASK_QUEUE}")
        print(f"  Namespace: {NAMESPACE}")
        print("  Registered: PaymentProcessingWorkflow")
        print("              validate_payment, execute_payment")
        print("  Nexus: ComplianceNexusService -> compliance-endpoint")
        print("=========================================================")
        await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
