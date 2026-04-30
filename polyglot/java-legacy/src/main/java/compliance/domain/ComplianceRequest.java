package compliance.domain;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Input to the compliance check.
 * Sent by the Payments team to the Compliance team.
 *
 * JSON keys use snake_case so Python callers can deserialize successfully.
 */
public class ComplianceRequest {
    private String transactionId;
    private double amount;
    private String senderCountry;
    private String receiverCountry;
    private String description;

    public ComplianceRequest() {}

    @JsonCreator(mode = JsonCreator.Mode.PROPERTIES)
    public ComplianceRequest(
            @JsonProperty("transaction_id") String transactionId,
            @JsonProperty("amount") double amount,
            @JsonProperty("sender_country") String senderCountry,
            @JsonProperty("receiver_country") String receiverCountry,
            @JsonProperty("description") String description) {
        this.transactionId = transactionId;
        this.amount = amount;
        this.senderCountry = senderCountry;
        this.receiverCountry = receiverCountry;
        this.description = description;
    }

    @JsonProperty("transaction_id")
    public String getTransactionId() { return transactionId; }

    @JsonProperty("amount")
    public double getAmount() { return amount; }

    @JsonProperty("sender_country")
    public String getSenderCountry() { return senderCountry; }

    @JsonProperty("receiver_country")
    public String getReceiverCountry() { return receiverCountry; }

    @JsonProperty("description")
    public String getDescription() { return description; }
}
