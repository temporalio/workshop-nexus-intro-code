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
    """Compliance team's worker - handles Nexus requests from Payments.

    Task queue: "compliance-risk"

    Registers three things:
      1. ComplianceWorkflow - the workflow that wraps the activity
      2. check_compliance activity - the activity that runs the checker
      3. ComplianceNexusServiceHandler - the Nexus handler that launches the workflow
    """
    client = await Client.connect("localhost:7233", namespace=NAMESPACE)

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        worker = Worker(
            client,
            task_queue=TASK_QUEUE,
            workflows=[ComplianceWorkflow],
            activities=[check_compliance],
            activity_executor=executor,
            nexus_service_handlers=[ComplianceNexusServiceHandler()],
        )
        print("=========================================================")
        print(f"  Compliance Worker started on: {TASK_QUEUE}")
        print(f"  Namespace: {NAMESPACE}")
        print("  Registered: ComplianceWorkflow, check_compliance, ComplianceNexusServiceHandler")
        print("=========================================================")
        await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
