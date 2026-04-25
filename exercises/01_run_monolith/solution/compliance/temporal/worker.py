# ===================================================================
#  TODO 3: Create the Compliance team's worker
# ===================================================================
#
# In this chapter the worker only needs to register the Nexus service handler.
# Sync handlers don't need a workflow or activity behind them - they run
# whatever code they want (within the 10s deadline) and return a result.
#
# When Ch 5 introduces the workflow-backed compliance check, we'll register
# workflows and activities here too.
#
#   1. nexus_service_handlers=[ComplianceNexusServiceHandler()]
#
# Task queue: "compliance-risk"
# This MUST match what you set as --target-task-queue when creating
# the Nexus endpoint via the CLI. If they don't match, calls fail.

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from compliance.temporal.nexus_handler import ComplianceNexusServiceHandler

TASK_QUEUE = "compliance-risk"
NAMESPACE = "compliance-namespace"


async def main() -> None:
    """Compliance team's worker - handles sync Nexus requests from Payments."""
    client = await Client.connect("localhost:7233", namespace=NAMESPACE)

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        # TODO 3: Register the Nexus service handler
        # nexus_service_handlers=[ComplianceNexusServiceHandler()],
    )
    print("=========================================================")
    print(f"  Compliance Worker started on: {TASK_QUEUE}")
    print(f"  Namespace: {NAMESPACE}")
    print("=========================================================")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
