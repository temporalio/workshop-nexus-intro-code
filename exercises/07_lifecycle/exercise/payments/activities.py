import random
import time

from temporalio import activity

from payments.models import PaymentRequest

@activity.defn
def validate_payment(request: PaymentRequest) -> bool:
    """Validate payment accounts and amount before execution."""
    if request.amount <= 0:
        print(f"[Payment] REJECTED: Invalid amount for {request.transaction_id}")
        return False
    if not request.sender_account or not request.receiver_account:
        print(f"[Payment] REJECTED: Missing account info for {request.transaction_id}")
        return False
    print(f"[Payment] Validation passed for {request.transaction_id}")
    return True

@activity.defn
def execute_payment(request: PaymentRequest) -> str:
    """Execute the payment through the gateway. May fail transiently - Temporal retries."""
    print(
        f"[Payment] Processing {request.transaction_id}"
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
    print(f"[Payment] Payment executed: {confirmation_number}")
    return confirmation_number
