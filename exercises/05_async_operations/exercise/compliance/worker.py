import asyncio
import concurrent.futures

from temporalio.client import Client
from temporalio.worker import Worker

from compliance.activities import check_compliance
from compliance.models import TASK_QUEUE
from compliance.service_handler import ComplianceNexusServiceHandler
from compliance.workflows import ComplianceWorkflow

NAMESPACE = "compliance-namespace"

async def main() -> None:
    """Compliance team's worker - hosts ComplianceWorkflow + check_compliance activity + Nexus handler."""
    client = await Client.connect("localhost:7233", namespace=NAMESPACE)

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        # TODO 8: Add three arguments to this Worker(...) call so it registers
        # ComplianceWorkflow, the check_compliance activity, and the executor
        # that runs the sync activity. See the assignment for the exact lines.
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
