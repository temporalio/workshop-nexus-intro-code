import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from compliance.models import TASK_QUEUE
from compliance.service_handler import ComplianceNexusServiceHandler

NAMESPACE = "compliance-namespace"

async def main() -> None:
    """Compliance team's worker - handles sync Nexus requests from Payments."""
    client = await Client.connect("localhost:7233", namespace=NAMESPACE)

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        # TODO 3 (Chapter 3): Add the nexus_service_handlers argument so this Worker registers the handler.
    )
    print("=========================================================")
    print(f"  Compliance Worker started on: {TASK_QUEUE}")
    print(f"  Namespace: {NAMESPACE}")
    print("=========================================================")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
