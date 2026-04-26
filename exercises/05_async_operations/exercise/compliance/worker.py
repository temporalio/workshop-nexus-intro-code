import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from compliance.models import TASK_QUEUE
from compliance.service_handler import ComplianceNexusServiceHandler

NAMESPACE = "compliance-namespace"

async def main() -> None:
    """Compliance team's worker - hosts ComplianceWorkflow + check_compliance activity + Nexus handler."""
    client = await Client.connect("localhost:7233", namespace=NAMESPACE)

    # TODO 8 (Chapter 5, Part C): Register ComplianceWorkflow and check_compliance on the worker.
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        nexus_service_handlers=[ComplianceNexusServiceHandler()],
    )
    print("=========================================================")
    print(f"  Compliance Worker started on: {TASK_QUEUE}")
    print(f"  Namespace: {NAMESPACE}")
    print("=========================================================")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
