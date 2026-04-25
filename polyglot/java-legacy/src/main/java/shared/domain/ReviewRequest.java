package shared.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Request data for submitting a human review decision via Nexus.
 *
 * Used by ReviewCallerWorkflow to call the submit_review Nexus operation.
 * The Compliance team's sync Nexus handler receives this and sends a Workflow
 * Update to the running ComplianceWorkflow.
 *
 * JSON keys use snake_case so Python callers can deserialize successfully.
 */
public class ReviewRequest {

    private String transactionId;
    private boolean approved;
    private String explanation;

    public ReviewRequest() {}

    @JsonCreator(mode = JsonCreator.Mode.PROPERTIES)
    public ReviewRequest(
            @JsonProperty("transaction_id") String transactionId,
            @JsonProperty("approved") boolean approved,
            @JsonProperty("explanation") String explanation) {
        this.transactionId = transactionId;
        this.approved = approved;
        this.explanation = explanation;
    }

    @JsonProperty("transaction_id")
    public String getTransactionId() { return transactionId; }
    public void setTransactionId(String transactionId) { this.transactionId = transactionId; }

    @JsonProperty("approved")
    public boolean isApproved() { return approved; }
    public void setApproved(boolean approved) { this.approved = approved; }

    @JsonProperty("explanation")
    public String getExplanation() { return explanation; }
    public void setExplanation(String explanation) { this.explanation = explanation; }
}
