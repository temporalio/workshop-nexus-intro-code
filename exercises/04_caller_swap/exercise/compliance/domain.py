from dataclasses import dataclass


@dataclass
class ComplianceRequest:
    """Input to the compliance check.
    Sent by the Payments team to the Compliance team.
    """

    transaction_id: str = ""
    amount: float = 0.0
    sender_country: str = ""
    receiver_country: str = ""
    description: str = ""


@dataclass
class ComplianceResult:
    """Result of a compliance check.
    Returned by the Compliance team to the Payments team.

    Fields:
      approved    - true = proceed with payment, false = block it
      risk_level  - "LOW", "MEDIUM", or "HIGH"
      explanation - one-line explanation of the decision
    """

    transaction_id: str = ""
    approved: bool = False
    risk_level: str = ""  # "LOW", "MEDIUM", "HIGH"
    explanation: str = ""

    def __str__(self) -> str:
        return (
            f"ComplianceResult{{txn={self.transaction_id}, approved={self.approved}, "
            f"risk={self.risk_level}, explanation='{self.explanation}'}}"
        )
