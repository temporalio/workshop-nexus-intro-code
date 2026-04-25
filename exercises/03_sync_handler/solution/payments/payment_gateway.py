import random
import time

from payments.domain import PaymentRequest


def validate_payment(request: PaymentRequest) -> bool:
    """Validate payment accounts and amount."""
    if request.amount <= 0:
        print(f"[PaymentGateway] REJECTED: Invalid amount for {request.transaction_id}")
        return False
    if not request.sender_account or not request.receiver_account:
        print(f"[PaymentGateway] REJECTED: Missing account info for {request.transaction_id}")
        return False
    print(f"[PaymentGateway] Validation passed for {request.transaction_id}")
    return True


def execute_payment(request: PaymentRequest) -> str:
    """Simulate payment execution with processing delay and occasional failures."""
    print(
        f"[PaymentGateway] Processing {request.transaction_id}"
        f" | ${request.amount:.2f}"
        f" | {request.sender_country} -> {request.receiver_country}"
    )

    # Simulate processing time
    time.sleep(0.5 + random.random() * 0.5)

    # Simulate occasional gateway failures (10% chance) - Temporal retries automatically
    if random.random() < 0.10:
        raise RuntimeError(
            f"Payment gateway timeout for {request.transaction_id}"
            " - connection to banking network failed"
        )

    confirmation_number = f"CONF-{request.transaction_id}-{int(time.time() * 1000)}"
    print(f"[PaymentGateway] Payment executed: {confirmation_number}")
    return confirmation_number
