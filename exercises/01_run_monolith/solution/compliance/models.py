from dataclasses import dataclass

TASK_QUEUE = "compliance-risk"

@dataclass
class ComplianceRequest:
    """Input to the compliance check.

    Sent by the Payments team to the Compliance team.
    """

    transaction_id: str
    amount: float
    sender_country: str
    receiver_country: str
    description: str

@dataclass
class ComplianceResult:
    """Result of a compliance check.

    Returned by the Compliance team to the Payments team.

    Fields:
      approved    - True = proceed with payment, False = block it
      risk_level  - "LOW", "MEDIUM", or "HIGH"
      explanation - one-line explanation of the decision
    """

    transaction_id: str
    approved: bool
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    explanation: str
