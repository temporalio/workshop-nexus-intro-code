package payments.temporal;

import compliance.domain.ComplianceResult;
import io.temporal.client.WorkflowClient;
import io.temporal.client.WorkflowClientOptions;
import io.temporal.client.WorkflowOptions;
import io.temporal.serviceclient.WorkflowServiceStubs;
import payments.Shared;
import shared.domain.ReviewRequest;

/**
 * [GIVEN] Starts a ReviewCallerWorkflow to approve TXN-B via Nexus.
 *
 * Instead of running 'temporal workflow update execute' directly, this starter
 * triggers a ReviewCallerWorkflow that calls the submitReview Nexus operation.
 * The Compliance team's sync handler forwards the decision to the running
 * ComplianceWorkflow as a Workflow Update.
 *
 * Change 'approved' to false below to see the denial path.
 */
public class ReviewStarter {

    public static void main(String[] args) {
        System.out.println("==========================================================");
        System.out.println("  REVIEW STARTER — Submitting review for TXN-B via Nexus");
        System.out.println("==========================================================\n");

        WorkflowServiceStubs service = WorkflowServiceStubs.newLocalServiceStubs();
        WorkflowClientOptions clientOptions = WorkflowClientOptions.newBuilder()
                .setNamespace("payments-namespace")
                .build();
        WorkflowClient client = WorkflowClient.newInstance(service, clientOptions);

        // Change approved to false to deny instead
        ReviewRequest request = new ReviewRequest("TXN-B", true, "Approved after manual review");

        ReviewCallerWorkflow workflow = client.newWorkflowStub(
                ReviewCallerWorkflow.class,
                WorkflowOptions.newBuilder()
                        .setTaskQueue(Shared.TASK_QUEUE)
                        .setWorkflowId("review-TXN-B")
                        .build());

        System.out.println("  Submitting review for TXN-B via Nexus...");
        System.out.println("  Approved: " + request.isApproved());
        System.out.println("  Explanation: " + request.getExplanation());
        System.out.println();

        ComplianceResult result = workflow.submitReview(request);

        System.out.println("  Review result: " + (result.isApproved() ? "✅ APPROVED" : "🚫 DENIED"));
        System.out.println("  Risk level:    " + result.getRiskLevel());
        System.out.println("  Explanation:   " + result.getExplanation());
        System.out.println();
        System.out.println("  TXN-B review submitted! The payment workflow will now complete.");
        System.out.println("==========================================================");

        System.exit(0);
    }
}
