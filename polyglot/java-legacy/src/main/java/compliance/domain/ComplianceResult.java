package compliance.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Result of a compliance check.
 * Returned by the Compliance team to the Payments team.
 *
 * JSON keys use snake_case so Python callers can deserialize successfully.
 *
 * Fields:
 *   approved    - true = proceed with payment, false = block it
 *   risk_level  - "LOW", "MEDIUM", or "HIGH"
 *   explanation - one-line explanation of the decision
 */
public class ComplianceResult {
    private String transactionId;
    private boolean approved;
    private String riskLevel;
    private String explanation;

    public ComplianceResult() {}

    @JsonCreator(mode = JsonCreator.Mode.PROPERTIES)
    public ComplianceResult(
            @JsonProperty("transaction_id") String transactionId,
            @JsonProperty("approved") boolean approved,
            @JsonProperty("risk_level") String riskLevel,
            @JsonProperty("explanation") String explanation) {
        this.transactionId = transactionId;
        this.approved = approved;
        this.riskLevel = riskLevel;
        this.explanation = explanation;
    }

    @JsonProperty("transaction_id")
    public String getTransactionId() { return transactionId; }

    @JsonProperty("approved")
    public boolean isApproved() { return approved; }

    @JsonProperty("risk_level")
    public String getRiskLevel() { return riskLevel; }

    @JsonProperty("explanation")
    public String getExplanation() { return explanation; }

    @Override
    public String toString() {
        return String.format("ComplianceResult{txn=%s, approved=%s, risk=%s, explanation='%s'}",
                transactionId, approved, riskLevel, explanation);
    }
}
