import asyncio

from temporalio.client import Client, WorkflowFailureError

from payments.models import TASK_QUEUE, PaymentRequest
from payments.workflows import PaymentProcessingWorkflow

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
    print("  Starting payment-ch07-TXN-FAIL-NONRETRY-1.")
    print("  The compliance handler raises nexusrpc.OperationError.")
    print("  Expect: the NexusOperationError propagates out of PaymentProcessingWorkflow")
    print("  and the Workflow Execution ends in the Failed state with no retries.")
    print()
    try:
        await asyncio.wait_for(
            client.execute_workflow(
                PaymentProcessingWorkflow.process_payment,
                request("TXN-FAIL-NONRETRY-1"),
                id="payment-ch07-TXN-FAIL-NONRETRY-1",
                task_queue=TASK_QUEUE,
            ),
            timeout=20,
        )
        print("  Unexpected: workflow completed successfully.")
    except WorkflowFailureError as exc:
        print(f"  Workflow failed as expected: {type(exc).__name__}: {exc}")
        if exc.cause is not None:
            print(f"  Caused by: {type(exc.cause).__name__}: {exc.cause}")
        print("  Confirmed: the Nexus operation failed with no retries.")
    print(f"  Inspect:")
    print(f"    temporal workflow show -w payment-ch07-TXN-FAIL-NONRETRY-1 -n {NAMESPACE}")

async def scenario_retryable(client: Client) -> None:
    banner("Scenario B: retryable HandlerError (BackingOff)")
    print("  Starting payment-ch07-TXN-FAIL-RETRY-1.")
    print("  The compliance handler raises nexusrpc.HandlerError(INTERNAL) on every call.")
    print("  The Nexus machinery treats this as retryable: Pending Operations show")
    print("  State: BackingOff and Attempt climbs.")
    print()
    handle = await client.start_workflow(
        PaymentProcessingWorkflow.process_payment,
        request("TXN-FAIL-RETRY-1"),
        id="payment-ch07-TXN-FAIL-RETRY-1",
        task_queue=TASK_QUEUE,
    )
    print("  Workflow started. Waiting 20 seconds while retries accumulate.")
    print(f"  In another terminal, run:")
    print(f"    temporal workflow describe -w payment-ch07-TXN-FAIL-RETRY-1 -n {NAMESPACE}")
    await asyncio.sleep(20)
    print("  Terminating to free the slot for the next scenario (this is a demo,")
    print("  in production you would let it ride out the schedule_to_close_timeout).")
    print("  We use terminate() here rather than cancel() because the Nexus")
    print("  operation is in BackingOff and cancellation would wait for the handler")
    print("  to acknowledge - the cancellation lesson is in Scenario C below.")
    try:
        await handle.terminate(reason="lifecycle scenario cleanup")
    except Exception as exc:
        print(f"  Terminate raised: {type(exc).__name__}")

async def scenario_cancellation(client: Client) -> None:
    banner("Scenario C: caller-driven cancellation")
    print("  Starting payment-ch07-TXN-CANCEL-1 ($12,000, MEDIUM risk via the")
    print("  amount-above-$10K rule arm; the request body is domestic US-to-US).")
    print("  ComplianceWorkflow classifies the risk as MEDIUM, sleeps 10 seconds,")
    print("  then waits for a human-review Update. We cancel the payment workflow")
    print("  during that pause and the cancellation propagates through the Nexus")
    print("  operation to ComplianceWorkflow.")
    print()
    handle = await client.start_workflow(
        PaymentProcessingWorkflow.process_payment,
        request("TXN-CANCEL-1", amount=12000.0),
        id="payment-ch07-TXN-CANCEL-1",
        task_queue=TASK_QUEUE,
    )
    await asyncio.sleep(3)
    print("  Cancelling payment-ch07-TXN-CANCEL-1.")
    try:
        await handle.cancel()
    except Exception as exc:
        print(f"  Cancel raised: {type(exc).__name__}")
    print("  Cancellation requested. Inspect both sides after a few seconds:")
    print(f"    temporal workflow describe -w payment-ch07-TXN-CANCEL-1   -n {NAMESPACE}")
    print(f"    temporal workflow describe -w compliance-ch07-TXN-CANCEL-1 -n compliance-namespace")
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
    for transaction_index in range(1, 7):
        wid = f"payment-ch07-TXN-CIRCUIT-{transaction_index}"
        handle = await client.start_workflow(
            PaymentProcessingWorkflow.process_payment,
            request(f"TXN-CIRCUIT-{transaction_index}"),
            id=wid,
            task_queue=TASK_QUEUE,
        )
        handles.append(handle)
        print(f"  Started {wid}")
    print()
    print("  Waiting 12 seconds for retries to accumulate and the breaker to trip.")
    await asyncio.sleep(12)
    print()
    print("  Inspect circuit-breaker state on any of the workflows:")
    for transaction_index in (1, 5, 6):
        print(f"    temporal workflow describe -w payment-ch07-TXN-CIRCUIT-{transaction_index} -n {NAMESPACE}")
    print()
    print("  Terminating all six so they don't keep retrying.")
    print("  As in Scenario B, terminate() is the right cleanup here because the")
    print("  Nexus operations are blocked on the open circuit breaker and a graceful")
    print("  cancel would wait for the breaker to half-open before propagating.")
    for handle in handles:
        try:
            await handle.terminate(reason="lifecycle scenario cleanup")
        except Exception:
            pass

async def pause_for_inspection(scenario: str) -> None:
    """Pause until the attendee presses Enter, so they can run
    `temporal workflow describe` without the next scenario stepping on
    the workflow they're inspecting.
    """
    print()
    print(f"  Scenario {scenario} done. Inspect the workflow above when you")
    print(f"  are ready, then press Enter to continue to the next scenario.")
    await asyncio.to_thread(input, "")

async def main() -> None:
    client = await Client.connect("localhost:7233", namespace=NAMESPACE)
    await scenario_non_retryable(client)
    await pause_for_inspection("A")
    await scenario_retryable(client)
    await pause_for_inspection("B")
    await scenario_cancellation(client)
    await pause_for_inspection("C")
    await scenario_circuit_breaker(client)
    print()
    print("==========================================================")
    print("  All lifecycle scenarios run. Open http://localhost:8233")
    print("  to inspect each workflow's history and pending operations.")
    print("==========================================================")

if __name__ == "__main__":
    asyncio.run(main())
