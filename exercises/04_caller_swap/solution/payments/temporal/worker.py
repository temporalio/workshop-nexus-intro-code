import asyncio
import concurrent.futures

from temporalio.client import Client
from temporalio.worker import Worker

from payments.domain import TASK_QUEUE
from payments.temporal.activities import execute_payment, validate_payment
from payments.temporal.workflows import PaymentProcessingWorkflow

NAMESPACE = "payments-namespace"


async def main() -> None:
    """Payments worker after the caller swap.

    Compliance check is no longer a local activity - it goes through Nexus to the
    Compliance worker. The ReviewCallerWorkflow (which submits human review decisions
    via Nexus) is introduced in Ch 5 alongside the workflow-backed compliance check.
    """
    client = await Client.connect("localhost:7233", namespace=NAMESPACE)

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        worker = Worker(
            client,
            task_queue=TASK_QUEUE,
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
