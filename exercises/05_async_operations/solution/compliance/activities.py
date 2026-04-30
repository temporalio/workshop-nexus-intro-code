from temporalio import activity

from compliance.models import ComplianceRequest, ComplianceResult

SANCTIONED_COUNTRIES = {"North Korea", "Iran", "Cuba", "Syria", "Venezuela"}
COMMON_COUNTRIES = {"US", "UK", "Canada", "Germany", "France", "Japan", "Australia"}

@activity.defn
def check_compliance(request: ComplianceRequest) -> ComplianceResult:
    """Run the deterministic, rule-based compliance check.

    Rules:
      - OFAC sanctioned countries -> HIGH risk, blocked
      - Amount > $50,000 -> HIGH risk, blocked
      - Amount > $10,000 or international to unusual jurisdiction -> MEDIUM risk, approved with note
      - Everything else -> LOW risk, approved
    """
    print(
        f"[Compliance] Evaluating {request.transaction_id}"
        f" | ${request.amount:.2f}"
        f" | {request.sender_country} -> {request.receiver_country}"
    )

    # Rule 1: Sanctioned country -> HIGH risk, blocked
    if (
        request.receiver_country in SANCTIONED_COUNTRIES
        or request.sender_country in SANCTIONED_COUNTRIES
    ):
        return ComplianceResult(
            transaction_id=request.transaction_id,
            approved=False,
            risk_level="HIGH",
            explanation="Destination/source country is OFAC-sanctioned. Transaction blocked per regulatory requirements.",
        )

    # Rule 2: Very high amount -> HIGH risk, blocked
    if request.amount > 50000:
        return ComplianceResult(
            transaction_id=request.transaction_id,
            approved=False,
            risk_level="HIGH",
            explanation="Transaction amount exceeds $50,000 threshold. Requires enhanced due diligence review.",
        )

    # Rule 3: Amount > $10K or international to unusual jurisdiction -> MEDIUM risk
    is_international = request.sender_country != request.receiver_country
    is_unusual_jurisdiction = (
        is_international and request.receiver_country not in COMMON_COUNTRIES
    )

    if request.amount > 10000 or is_unusual_jurisdiction:
        # Branch the explanation by which arm fired so the result tells
        # an honest story to whoever reads the workflow's output.
        if request.amount > 10000 and is_unusual_jurisdiction:
            explanation = (
                f"Amount above $10K threshold and international transfer to "
                f"unusual jurisdiction ({request.receiver_country}). Approved "
                f"with AML monitoring note."
            )
        elif request.amount > 10000:
            explanation = "Amount above $10K threshold. Approved with AML monitoring note."
        else:
            explanation = (
                f"International transfer to unusual jurisdiction "
                f"({request.receiver_country}). Approved with AML monitoring note."
            )
        return ComplianceResult(
            transaction_id=request.transaction_id,
            approved=True,
            risk_level="MEDIUM",
            explanation=explanation,
        )

    # Rule 4: Low risk - routine transaction
    return ComplianceResult(
        transaction_id=request.transaction_id,
        approved=True,
        risk_level="LOW",
        explanation="Routine domestic/standard international transfer. No regulatory concerns.",
    )
