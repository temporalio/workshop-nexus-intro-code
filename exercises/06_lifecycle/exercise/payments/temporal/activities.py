from temporalio import activity

from payments.domain import PaymentRequest
from payments.payment_gateway import (
    execute_payment as _execute_payment,
    validate_payment as _validate_payment,
)


@activity.defn
def validate_payment(request: PaymentRequest) -> bool:
    """Validate payment accounts and amount."""
    return _validate_payment(request)


@activity.defn
def execute_payment(request: PaymentRequest) -> str:
    """Execute payment through gateway. May fail transiently - Temporal retries."""
    return _execute_payment(request)
