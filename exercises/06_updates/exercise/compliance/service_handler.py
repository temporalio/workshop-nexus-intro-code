import nexusrpc.handler
from temporalio import nexus
from temporalio.common import WorkflowIDConflictPolicy

# TODO 11a: Add the import the submit_review body below needs to type the workflow
# handle returned by the Temporal client. See the README.

from compliance.models import ComplianceRequest, ComplianceResult
from compliance.workflows import ComplianceWorkflow
from shared.models import ReviewRequest
from shared.service import ComplianceNexusService

@nexusrpc.handler.service_handler(service=ComplianceNexusService)
class ComplianceNexusServiceHandler:
    """Nexus service handler.

    check_compliance: async (workflow_run_operation) - starts a new ComplianceWorkflow.
    submit_review: stub. TODO 11 turns it into a real Update sender.
    """

    @nexus.workflow_run_operation
    async def check_compliance(
        self, ctx: nexus.WorkflowRunOperationContext, input: ComplianceRequest
    ) -> nexus.WorkflowHandle[ComplianceResult]:
        return await ctx.start_workflow(
            ComplianceWorkflow.run,
            input,
            id=f"compliance-ch06-{input.transaction_id}",
            id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
        )

    @nexusrpc.handler.sync_operation
    async def submit_review(
        self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
    ) -> ComplianceResult:
        # TODO 11b: Replace this stub with a real Update sender that finds the running
        # ComplianceWorkflow by id and sends it the `review` Update. See the README.
        pass
