import asyncio

from temporalio.client import Client

from payments.domain import TASK_QUEUE, PaymentRequest, PaymentResult
from payments.temporal.workflows import PaymentProcessingWorkflow

NAMESPACE = "payments-namespace"


def request(transaction_id: str, amount: float = 250.0) -> PaymentRequest:
    """Build a routine PaymentRequest. The transaction_id drives the lifecycle scenario."""
    return PaymentRequest(
        transaction_id=transaction_id,
        amount=amount,
        currency="USD",
        sender_country="US",
        receiver_country="US",
        description="Lifecycle scenario",
        sender_account="ACC-LIFE-1",
        receiver_account="ACC-LIFE-2",
    )


def banner(title: str) -> None:
    print()
    print("==========================================================")
    print(f"  {title}")
    print("==========================================================")


async def scenario_non_retryable(client: Client) -> None:
    banner("Scenario A: non-retryable OperationError")
    print("  Starting payment-TXN-FAIL-NONRETRY-1.")
    print("  The compliance handler raises nexusrpc.OperationError.")
    print("  Expect: PaymentProcessingWorkflow's try/except catches it and")
    print("  returns status=FAILED. The Nexus operation is marked Failed with no retries.")
    print()
    try:
        result: PaymentResult = await asyncio.wait_for(
            client.execute_workflow(
                PaymentProcessingWorkflow.process_payment,
                request("TXN-FAIL-NONRETRY-1"),
                id="payment-TXN-FAIL-NONRETRY-1",
                task_queue=TASK_QUEUE,
            ),
            timeout=20,
        )
        print(f"  Status: {result.status}")
        print(f"  Error : {result.error or '(none)'}")
        if result.status == "FAILED":
            print("  Confirmed: workflow saw the Nexus operation fail with no retries.")
    except Exception as exc:
        print(f"  Exception: {type(exc).__name__}: {exc}")
    print(f"  Inspect:")
    print(f"    temporal workflow show -w payment-TXN-FAIL-NONRETRY-1 -n {NAMESPACE}")


async def scenario_retryable(client: Client) -> None:
    banner("Scenario B: retryable HandlerError (BackingOff)")
    print("  Starting payment-TXN-FAIL-RETRY-1.")
    print("  The compliance handler raises nexusrpc.HandlerError(INTERNAL) on every call.")
    print("  The Nexus machinery treats this as retryable: Pending Operations show")
    print("  State: BackingOff and Attempt climbs.")
    print()
    handle = await client.start_workflow(
        PaymentProcessingWorkflow.process_payment,
        request("TXN-FAIL-RETRY-1"),
        id="payment-TXN-FAIL-RETRY-1",
        task_queue=TASK_QUEUE,
    )
    print("  Workflow started. Waiting 15 seconds while retries accumulate.")
    print(f"  In another terminal, run:")
    print(f"    temporal workflow describe -w payment-TXN-FAIL-RETRY-1 -n {NAMESPACE}")
    await asyncio.sleep(15)
    print("  Terminating to free the slot for the next scenario (this is a demo,")
    print("  in production you would let it ride out the schedule_to_close_timeout).")
    try:
        await handle.terminate(reason="lifecycle scenario cleanup")
    except Exception as exc:
        print(f"  Terminate raised: {type(exc).__name__}")


async def scenario_cancellation(client: Client) -> None:
    banner("Scenario C: caller-driven cancellation")
    print("  Starting payment-TXN-CANCEL-1 (a routine LOW-risk transaction).")
    print("  ComplianceWorkflow runs an activity then sleeps 10 seconds. We cancel")
    print("  the payment workflow during that sleep and the cancellation propagates")
    print("  through the Nexus operation to ComplianceWorkflow.")
    print()
    handle = await client.start_workflow(
        PaymentProcessingWorkflow.process_payment,
        request("TXN-CANCEL-1"),
        id="payment-TXN-CANCEL-1",
        task_queue=TASK_QUEUE,
    )
    await asyncio.sleep(3)
    print("  Cancelling payment-TXN-CANCEL-1.")
    try:
        await handle.cancel()
    except Exception as exc:
        print(f"  Cancel raised: {type(exc).__name__}")
    print("  Cancellation requested. Inspect both sides after a few seconds:")
    print(f"    temporal workflow describe -w payment-TXN-CANCEL-1   -n {NAMESPACE}")
    print(f"    temporal workflow describe -w compliance-TXN-CANCEL-1 -n compliance-namespace")
    print("  See the samples-python nexus_cancel sample for the in-workflow cancellation")
    print("  pattern (start_operation + task.cancel() + asyncio.shield in handler).")


async def scenario_circuit_breaker(client: Client) -> None:
    banner("Scenario D: circuit breaker")
    print("  Sending 6 TXN-CIRCUIT-* transactions back to back.")
    print("  Each fails with a retryable HandlerError. After 5 consecutive retryable")
    print("  failures on the same caller-Namespace/Endpoint pair, the circuit breaker")
    print("  opens for ~60 seconds. Subsequent operations show State: Blocked with")
    print("  BlockedReason: The circuit breaker is open.")
    print()
    handles = []
    for i in range(1, 7):
        wid = f"payment-TXN-CIRCUIT-{i}"
        h = await client.start_workflow(
            PaymentProcessingWorkflow.process_payment,
            request(f"TXN-CIRCUIT-{i}"),
            id=wid,
            task_queue=TASK_QUEUE,
        )
        handles.append(h)
        print(f"  Started {wid}")
    print()
    print("  Waiting 12 seconds for retries to accumulate and the breaker to trip.")
    await asyncio.sleep(12)
    print()
    print("  Inspect circuit-breaker state on any of the workflows:")
    for i in (1, 5, 6):
        print(f"    temporal workflow describe -w payment-TXN-CIRCUIT-{i} -n {NAMESPACE}")
    print()
    print("  Terminating all six so they don't keep retrying.")
    for h in handles:
        try:
            await h.terminate(reason="lifecycle scenario cleanup")
        except Exception:
            pass


async def main() -> None:
    client = await Client.connect("localhost:7233", namespace=NAMESPACE)
    await scenario_non_retryable(client)
    await scenario_retryable(client)
    await scenario_cancellation(client)
    await scenario_circuit_breaker(client)
    print()
    print("==========================================================")
    print("  All lifecycle scenarios run. Open http://localhost:8233")
    print("  to inspect each workflow's history and pending operations.")
    print("==========================================================")


if __name__ == "__main__":
    asyncio.run(main())
