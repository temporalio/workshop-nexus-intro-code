from dataclasses import dataclass

TASK_QUEUE = "payments-processing"

@dataclass
class PaymentRequest:
    """A payment transaction to be processed."""

    transaction_id: str
    amount: float
    currency: str
    sender_country: str
    receiver_country: str
    description: str
    sender_account: str
    receiver_account: str

@dataclass
class PaymentResult:
    """Result of a payment workflow execution.

    status values:
      "COMPLETED"           - payment processed successfully
      "REJECTED"            - failed payment validation
      "DECLINED_COMPLIANCE" - compliance check returned approved=False
    """

    success: bool
    transaction_id: str
    status: str
    risk_level: str | None = None  # from compliance check: "LOW", "MEDIUM", "HIGH"
    explanation: str | None = None  # from compliance check explanation
    confirmation_number: str | None = None  # set when status == "COMPLETED"
    error: str | None = None
