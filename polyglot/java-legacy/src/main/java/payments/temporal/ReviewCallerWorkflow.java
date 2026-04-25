package payments.temporal;

import compliance.domain.ComplianceResult;
import io.temporal.workflow.WorkflowInterface;
import io.temporal.workflow.WorkflowMethod;
import shared.domain.ReviewRequest;

/**
 * [GIVEN] Caller workflow that submits a compliance review decision through Nexus.
 *
 * Instead of calling 'temporal workflow update execute' directly, the compliance
 * officer triggers this workflow. It routes the review through the Nexus endpoint,
 * respecting team boundaries — neither team needs to know the other's workflow IDs
 * or internal method names.
 *
 * This demonstrates the sync Nexus operation pattern: a short-lived operation that
 * interacts with an already-running workflow via a Workflow Update.
 */
@WorkflowInterface
public interface ReviewCallerWorkflow {

    @WorkflowMethod
    ComplianceResult submitReview(ReviewRequest request);
}
