package compliance;

import compliance.domain.ComplianceRequest;
import compliance.domain.ComplianceResult;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/**
 * [GIVEN] Rule-based compliance checker — deterministic, no API keys needed.
 *
 * Deterministic, rule-based compliance checker — no external API calls needed.
 * Same interface whether used as an Activity or behind a Nexus handler.
 *
 * Rules:
 *   - Amount > $50,000 → HIGH risk, blocked (TXN-C in the exercise hits this: $75K domestic)
 *   - OFAC sanctioned countries (Iran, Cuba, Syria, Venezuela) → HIGH risk, blocked
 *   - Amount > $10,000 or international to unusual jurisdiction → MEDIUM risk, approved with note
 *   - Everything else → LOW risk, approved
 *
 * Students use this class as-is — focus is on the Nexus boundary, not compliance logic.
 * To test the OFAC rule, try sending a transaction to "Iran" as the receiver country.
 */
public class ComplianceChecker {

    private static final Set<String> SANCTIONED_COUNTRIES = new HashSet<>(Arrays.asList(
            "North Korea", "Iran", "Cuba", "Syria", "Venezuela"
    ));

    private static final Set<String> COMMON_COUNTRIES = new HashSet<>(Arrays.asList(
            "US", "UK", "Canada", "Germany", "France", "Japan", "Australia"
    ));

    public ComplianceResult checkCompliance(ComplianceRequest request) {
        System.out.println("[ComplianceChecker] Evaluating " + request.getTransactionId()
                + " | $" + String.format("%.2f", request.getAmount())
                + " | " + request.getSenderCountry() + " -> " + request.getReceiverCountry());

        // Rule 1: Sanctioned country → HIGH risk, blocked
        if (SANCTIONED_COUNTRIES.contains(request.getReceiverCountry())
                || SANCTIONED_COUNTRIES.contains(request.getSenderCountry())) {
            return new ComplianceResult(
                    request.getTransactionId(),
                    false,
                    "HIGH",
                    "Destination/source country is OFAC-sanctioned. Transaction blocked per regulatory requirements."
            );
        }

        // Rule 2: Very high amount → HIGH risk, blocked
        if (request.getAmount() > 50000) {
            return new ComplianceResult(
                    request.getTransactionId(),
                    false,
                    "HIGH",
                    "Transaction amount exceeds $50,000 threshold. Requires enhanced due diligence review."
            );
        }

        // Rule 3: Amount > $10K or international to unusual jurisdiction → MEDIUM risk
        boolean isInternational = !request.getSenderCountry().equals(request.getReceiverCountry());
        boolean isUnusualJurisdiction = isInternational
                && !COMMON_COUNTRIES.contains(request.getReceiverCountry());

        if (request.getAmount() > 10000 || isUnusualJurisdiction) {
            // Branch the explanation by which arm fired so the result tells
            // an honest story to whoever reads the workflow's output.
            String explanation;
            if (request.getAmount() > 10000 && isUnusualJurisdiction) {
                explanation = "Amount above $10K threshold and international transfer to "
                        + "unusual jurisdiction (" + request.getReceiverCountry() + "). "
                        + "Approved with AML monitoring note.";
            } else if (request.getAmount() > 10000) {
                explanation = "Amount above $10K threshold. Approved with AML monitoring note.";
            } else {
                explanation = "International transfer to unusual jurisdiction ("
                        + request.getReceiverCountry() + "). Approved with AML monitoring note.";
            }
            return new ComplianceResult(
                    request.getTransactionId(),
                    true,
                    "MEDIUM",
                    explanation
            );
        }

        // Rule 4: Low risk — routine transaction
        return new ComplianceResult(
                request.getTransactionId(),
                true,
                "LOW",
                "Routine domestic/standard international transfer. No regulatory concerns."
        );
    }
}
