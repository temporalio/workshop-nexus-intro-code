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
        # TODO 3: Register the Nexus service handler on this Worker so it can serve operations on this task queue.
    )
    print("=========================================================")
    print(f"  Compliance Worker started on: {TASK_QUEUE}")
    print(f"  Namespace: {NAMESPACE}")
    print("  Registered: ComplianceNexusServiceHandler (sync only)")
    print("=========================================================")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
