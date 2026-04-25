# ===================================================================
#  MONOLITH VERSION - this works at Checkpoint 0.
# ===================================================================
#
# Currently this single worker handles EVERYTHING:
#   - PaymentProcessingWorkflow
#   - validate_payment + execute_payment activities
#   - check_compliance activity  (will move to its own worker)
#
# All on one task queue: "payments-processing"
#
# TODO 5: Remove check_compliance from the activities list
#
# After completing TODOs 1-4 and standing up the Compliance worker, the
# compliance check no longer runs locally. The Nexus call routes to the
# Compliance worker via the endpoint.
#
# CHANGE: Remove check_compliance from the activities list.
#   Currently:   activities=[validate_payment, execute_payment, check_compliance]
#   Change to:   activities=[validate_payment, execute_payment]

import asyncio
import concurrent.futures

from temporalio.client import Client
from temporalio.worker import Worker

from compliance.temporal.activities import check_compliance
from payments.domain import TASK_QUEUE
from payments.temporal.activities import execute_payment, validate_payment
from payments.temporal.workflows import PaymentProcessingWorkflow

NAMESPACE = "payments-namespace"


async def main() -> None:
    """Payments worker - monolith version with compliance activity."""
    client = await Client.connect("localhost:7233", namespace=NAMESPACE)

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        worker = Worker(
            client,
            task_queue=TASK_QUEUE,
            workflows=[PaymentProcessingWorkflow],
            # TODO 5: Remove check_compliance from this list after Nexus is wired up.
            # The compliance check now runs on the Compliance worker via Nexus.
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
