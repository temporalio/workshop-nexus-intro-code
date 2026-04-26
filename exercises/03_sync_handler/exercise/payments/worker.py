import asyncio
import concurrent.futures

from temporalio.client import Client
from temporalio.worker import Worker

from compliance.activities import check_compliance
from payments.activities import execute_payment, validate_payment
from payments.models import TASK_QUEUE
from payments.workflows import PaymentProcessingWorkflow

NAMESPACE = "payments-namespace"

async def main() -> None:
    """Payments worker - monolith version with compliance activity."""
    client = await Client.connect("localhost:7233", namespace=NAMESPACE)

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        worker = Worker(
            client,
            task_queue=TASK_QUEUE,
            workflows=[PaymentProcessingWorkflow],
            # TODO 5 (Chapter 4, Part B): Remove check_compliance from the activities list and the import above.
            activities=[validate_payment, execute_payment, check_compliance],
            activity_executor=executor,
        )
        print("=========================================================")
        print(f"  Payments Worker started on: {TASK_QUEUE}")
        print(f"  Namespace: {NAMESPACE}")
        print("  Registered: PaymentProcessingWorkflow")
        print("              validate_payment, execute_payment")
        print("              check_compliance (monolith - will decouple)")
        print("=========================================================")
        await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
