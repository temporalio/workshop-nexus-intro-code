package payments.temporal;

import compliance.domain.ComplianceResult;
import io.temporal.workflow.NexusOperationOptions;
import io.temporal.workflow.NexusServiceOptions;
import io.temporal.workflow.Workflow;
import shared.domain.ReviewRequest;
import shared.nexus.ComplianceNexusService;

import java.time.Duration;

/**
 * [GIVEN] Sends a compliance review decision through Nexus.
 *
 * Calls complianceService.submitReview() via a sync Nexus operation.
 * The Compliance team's handler (OperationHandler.sync) receives it,
 * looks up the compliance-{transactionId} workflow, and sends a Workflow
 * Update — all within the 10-second sync handler deadline.
 *
 * Endpoint mapping for "ComplianceNexusService" is configured in
 * PaymentsWorkerApp. No endpoint configuration needed here.
 */
public class ReviewCallerWorkflowImpl implements ReviewCallerWorkflow {

    private final ComplianceNexusService complianceService = Workflow.newNexusServiceStub(
            ComplianceNexusService.class,
            NexusServiceOptions.newBuilder()
                    .setOperationOptions(NexusOperationOptions.newBuilder()
                            .setScheduleToCloseTimeout(Duration.ofSeconds(10))
                            .build())
                    .build());

    @Override
    public ComplianceResult submitReview(ReviewRequest request) {
        return complianceService.submitReview(request);
    }
}
