package compliance.temporal.workflow;

import compliance.domain.ComplianceRequest;
import compliance.domain.ComplianceResult;
import io.temporal.workflow.UpdateMethod;
import io.temporal.workflow.UpdateValidatorMethod;
import io.temporal.workflow.WorkflowInterface;
import io.temporal.workflow.WorkflowMethod;

/**
 * Workflow that runs an automated compliance check and, for MEDIUM-risk
 * transactions, waits for a human reviewer to approve or deny.
 *
 * LOW risk  → auto-approved, returns immediately
 * HIGH risk → auto-denied, returns immediately
 * MEDIUM    → pauses, waits for review() Update
 */
@WorkflowInterface
public interface ComplianceWorkflow {

    @WorkflowMethod
    ComplianceResult run(ComplianceRequest request);

    @UpdateMethod
    ComplianceResult review(boolean approved, String explanation);

    @UpdateValidatorMethod(updateName = "review")
    void validateReview(boolean approved, String explanation);
}
