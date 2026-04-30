import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from compliance.models import TASK_QUEUE
from compliance.service_handler import ComplianceNexusServiceHandler

NAMESPACE = "compliance-namespace"

async def main() -> None:
    """Compliance team's worker - hosts ComplianceWorkflow + check_compliance activity + Nexus handler."""
    client = await Client.connect("localhost:7233", namespace=NAMESPACE)

    # TODO 8: Register ComplianceWorkflow and the check_compliance activity on this
    # Worker alongside the existing Nexus service handler, and supply an executor for
    # the sync activity. See the assignment for the wrapping pattern.
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
