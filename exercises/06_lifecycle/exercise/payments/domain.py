from dataclasses import dataclass, field


TASK_QUEUE = "payments-processing"


@dataclass
class PaymentRequest:
    """A payment transaction to be processed."""

    transaction_id: str = ""
    amount: float = 0.0
    currency: str = ""
    sender_country: str = ""
    receiver_country: str = ""
    description: str = ""
    sender_account: str = ""
    receiver_account: str = ""


@dataclass
class PaymentResult:
    """Result of a payment workflow execution.

    status values:
      "COMPLETED"           - payment processed successfully
      "REJECTED"            - failed payment validation
      "DECLINED_COMPLIANCE" - compliance check returned approved=false
      "FAILED"              - unexpected error
    """

    success: bool = False
    transaction_id: str = ""
    status: str = ""
    risk_level: str = ""  # from compliance check: "LOW", "MEDIUM", "HIGH"
    explanation: str = ""  # from compliance check explanation
    confirmation_number: str = ""  # set when status = COMPLETED
    error: str = ""
