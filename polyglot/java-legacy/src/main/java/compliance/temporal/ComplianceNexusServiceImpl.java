package compliance.temporal;

import compliance.domain.ComplianceRequest;
import compliance.domain.ComplianceResult;
import compliance.temporal.workflow.ComplianceWorkflow;
import io.nexusrpc.handler.OperationHandler;
import io.nexusrpc.handler.OperationImpl;
import io.nexusrpc.handler.ServiceImpl;
import io.temporal.client.WorkflowClient;
import io.temporal.client.WorkflowOptions;
import io.temporal.nexus.Nexus;
import io.temporal.nexus.WorkflowHandle;
import io.temporal.nexus.WorkflowRunOperation;
import shared.domain.ReviewRequest;
import shared.nexus.ComplianceNexusService;

/**
 * Nexus service handler — receives cross-team calls from Payments.
 *
 * Two handlers:
 *   - checkCompliance: async (fromWorkflowHandle) — starts a new ComplianceWorkflow
 *   - submitReview: sync (OperationHandler.sync) — sends Update to a running workflow
 */
@ServiceImpl(service = ComplianceNexusService.class)
public class ComplianceNexusServiceImpl {

    @OperationImpl
    public OperationHandler<ComplianceRequest, ComplianceResult> checkCompliance() {
        return WorkflowRunOperation.fromWorkflowHandle((ctx, details, input) -> {
            WorkflowClient client = Nexus.getOperationContext().getWorkflowClient();
            ComplianceWorkflow wf = client.newWorkflowStub(
                    ComplianceWorkflow.class,
                    WorkflowOptions.newBuilder()
                            .setTaskQueue("compliance-risk")
                            .setWorkflowId("compliance-" + input.getTransactionId())
                            .build());

            return WorkflowHandle.fromWorkflowMethod(wf::run, input);
        });
    }

    @OperationImpl
    public OperationHandler<ReviewRequest, ComplianceResult> submitReview() {
        return OperationHandler.sync((ctx, details, input) -> {
            WorkflowClient client = Nexus.getOperationContext().getWorkflowClient();
            ComplianceWorkflow wf = client.newWorkflowStub(
                    ComplianceWorkflow.class,
                    "compliance-" + input.getTransactionId());
            return wf.review(input.isApproved(), input.getExplanation());
        });
    }
}
