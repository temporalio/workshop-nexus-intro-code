package compliance.temporal.workflow;

import compliance.domain.ComplianceRequest;
import compliance.domain.ComplianceResult;
import compliance.temporal.activity.ComplianceActivity;
import io.temporal.activity.ActivityOptions;
import io.temporal.workflow.Workflow;

import java.time.Duration;

/**
 * Runs the automated compliance check, then conditionally waits for human review.
 *
 * LOW / HIGH risk → returns the automated result immediately.
 * MEDIUM risk     → pauses and waits for a review() Update to approve or deny.
 */
public class ComplianceWorkflowImpl implements ComplianceWorkflow {

    private ComplianceRequest request;
    private ComplianceResult autoResult;
    private ComplianceResult reviewResult = null;

    private final ComplianceActivity complianceActivity = Workflow.newActivityStub(
            ComplianceActivity.class,
            ActivityOptions.newBuilder()
                    .setStartToCloseTimeout(Duration.ofSeconds(30))
                    .build());

    @Override
    public ComplianceResult run(ComplianceRequest request) {
        this.request = request;

        // Step 1: Run automated compliance check
        autoResult = complianceActivity.checkCompliance(request);

        // Durable delay — demonstrates Nexus + Temporal durability.
        // Kill the compliance worker mid-sleep, restart it, and the workflow resumes automatically.
        Workflow.sleep(Duration.ofSeconds(10));

        // Step 2: LOW or HIGH risk → return immediately
        if (!"MEDIUM".equals(autoResult.getRiskLevel())) {
            return autoResult;
        }

        // Step 3: MEDIUM risk → wait for human review via Update
        Workflow.await(() -> reviewResult != null);
        return reviewResult;
    }

    @Override
    public ComplianceResult review(boolean approved, String explanation) {
        this.reviewResult = new ComplianceResult(
                request.getTransactionId(), approved, "MEDIUM", explanation);
        return reviewResult;
    }

    @Override
    public void validateReview(boolean approved, String explanation) {
        if (autoResult == null || !"MEDIUM".equals(autoResult.getRiskLevel())) {
            throw new IllegalStateException("Workflow is not awaiting review");
        }
        if (reviewResult != null) {
            throw new IllegalStateException("Review already submitted");
        }
    }
}
