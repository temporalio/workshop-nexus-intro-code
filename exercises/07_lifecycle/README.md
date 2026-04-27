# Chapter 7: Lifecycle Control: Cancellation, Errors, Circuit Breaker

In this chapter, you will exercise the production-readiness behaviors of Nexus operations: cancelling an in-flight async operation, returning retryable vs non-retryable errors from a handler, and watching the circuit breaker trip after a string of failures.

The compliance handler from Ch 5 (async) and Ch 6 (review path) already accepts normal transactions. For Ch 7, you will add three failure-injection branches at the top of `check_compliance`. Special `transaction_id` prefixes that the lifecycle starter sends will trigger each scenario. Cancellation needs no handler changes; it propagates automatically from a cancelled caller workflow.

By the end of this chapter, you will:

- Raise `nexusrpc.OperationError` (non-retryable) and observe `NexusOperationFailed` with no retries
- Raise `nexusrpc.HandlerError` with type `INTERNAL` (retryable) and observe Pending Operations in the `BackingOff` state with attempt count climbing
- Cancel an in-flight async Nexus operation from the caller side and watch the cancellation propagate to the underlying `ComplianceWorkflow`
- Trip the Nexus circuit breaker by sending several retryable failures in succession and observe `State: Blocked` with `BlockedReason: The circuit breaker is open`

Make your changes in `exercise/`. Look for `TODO 13` in `compliance/service_handler.py`. If you get stuck, compare with `solution/`.

## Part A: Add the failure-injection branches (TODO 13)

Open `compliance/service_handler.py`. Inside `check_compliance`, before the `start_workflow` call, add three branches:

```python
txn_id = input.transaction_id

if txn_id.startswith("TXN-FAIL-NONRETRY"):
    raise nexusrpc.OperationError(
        "Permanent compliance failure (non-retryable)",
        state=nexusrpc.OperationErrorState.FAILED,
    )
if txn_id.startswith("TXN-FAIL-RETRY") or txn_id.startswith("TXN-CIRCUIT"):
    raise nexusrpc.HandlerError(
        "Transient compliance failure (retryable)",
        type=nexusrpc.HandlerErrorType.INTERNAL,
    )
```

You also need to add a top-level `import nexusrpc` at the top of the file. (Strictly speaking, `import nexusrpc.handler` already binds the `nexusrpc` name and exposes `nexusrpc.OperationError`, but listing the top-level package explicitly makes the file's imports self-documenting.)

The branches are mutually exclusive with the normal `start_workflow` path. A normal transaction (TXN-A, TXN-B, TXN-C) hits none of the prefixes and runs as before.

## Part B: Run the lifecycle starter

`payments/lifecycle_starter.py` is provided. It runs four scenarios in order:

- **Scenario A** sends `TXN-FAIL-NONRETRY-1` and waits for the immediate failure.
- **Scenario B** sends `TXN-FAIL-RETRY-1`, lets it retry for ~20 seconds, then terminates it so the demo can move on. (We use `terminate` rather than `cancel` because the Nexus operation is in `BackingOff` and graceful cancellation would wait on the handler to acknowledge - the cancellation lesson is Scenario C, just below.)
- **Scenario C** sends `TXN-CANCEL-1` (a $12,000 international transfer -> MEDIUM risk), waits 3 seconds while the handler workflow is in its durable pause / awaiting-review window, then **cancels** the payment workflow. Cancellation propagates through the Nexus operation to the underlying `ComplianceWorkflow`, and both end in `Canceled`.
- **Scenario D** sends six `TXN-CIRCUIT-*` transactions back to back, then terminates them all after the breaker trips. (Same reason as Scenario B: the operations are blocked on the open circuit breaker, so terminate is faster than waiting for graceful cancellation to propagate.)

You need both workers running first. Three terminals from `exercises/07_lifecycle/exercise/`:

**Terminal 1, Compliance worker:**

```bash
uv run python -m compliance.worker
```

**Terminal 2, Payments worker:**

```bash
uv run python -m payments.worker
```

**Terminal 3, lifecycle starter:**

```bash
uv run python -m payments.lifecycle_starter
```

The starter runs all four scenarios in sequence (about 90 seconds end to end). Watch the output and watch the Web UI at http://localhost:8233 to follow each scenario.

## Part C: Inspect each scenario in the UI and CLI

### Scenario A: non-retryable error

In the `payments-namespace`, `payment-TXN-FAIL-NONRETRY-1` ends in `Failed` state. The `NexusOperationError` propagates out of `PaymentProcessingWorkflow` (the workflow does not catch it), so the Workflow Execution itself fails. Its Event History shows `NexusOperationScheduled` followed by `NexusOperationFailed` with no retries in between. The starter catches the resulting `WorkflowFailureError` and prints the `NexusOperationError` cause.

### Scenario B: retryable error with BackingOff

While the starter is in this scenario (~20 seconds), run:

```bash
temporal workflow describe -w payment-TXN-FAIL-RETRY-1 -n payments-namespace
```

You should see `Pending Nexus Operations` with `State: BackingOff` and `Attempt` increasing on each subsequent describe call. After ~20 seconds, the starter terminates the workflow so the demo can move on. The workflow ends in `Terminated` state. The cancellation-propagation lesson is in Scenario C, where the Nexus handler is in a state that can actually accept the cancel.

### Scenario C: cancellation propagation

After the starter ends Scenario C, look at both sides:

```bash
temporal workflow describe -w payment-TXN-CANCEL-1   -n payments-namespace
temporal workflow describe -w compliance-TXN-CANCEL-1 -n compliance-namespace
```

The payment workflow ends as `CancelRequested`/`Canceled`. The Nexus operation in the caller's history shows a `NexusOperationCanceled` event. The handler `ComplianceWorkflow` (in the compliance namespace) is also cancelled, even though we never told it directly. Cancellation flows through the Nexus boundary.

If you want to control how the caller waits for the cancellation, the available cancellation types on `nexus_client.execute_operation` are `ABANDON`, `TRY_CANCEL`, `WAIT_REQUESTED`, and `WAIT_COMPLETED`. The default is `WAIT_COMPLETED`. The lifecycle starter uses the default; experiment with the others to feel the trade-offs.

> Aside: the proto-level enum names (visible in core SDK source and some debug output) are `WAIT_CANCELLATION_REQUESTED` and `WAIT_CANCELLATION_COMPLETED`. The Python SDK exposes them as `WAIT_REQUESTED` / `WAIT_COMPLETED`, which is what `temporalio.workflow.NexusOperationCancellationType` ships.

### Scenario D: circuit breaker

While Scenario D is running (after the 12-second wait), run:

```bash
temporal workflow describe -w payment-TXN-CIRCUIT-6 -n payments-namespace
```

The first few `TXN-CIRCUIT-*` workflows show `State: BackingOff`. Once the breaker has tripped (around the 5th retryable failure on this caller-Namespace/Endpoint pair), the later ones show:

```
State           Blocked
BlockedReason   The circuit breaker is open.
```

The breaker stays open for ~60 seconds, then enters half-open and probes with a single request. If that request succeeds, the breaker closes again. The starter terminates all six workflows at the end so they do not keep retrying; each ends in `Terminated` state. (Same rationale as Scenario B: graceful cancellation would wait on the open breaker; terminate is the right tool for the cleanup here.)

## Take Aways

Nexus errors split into two categories on the wire: retryable (`HandlerError` with retryable type, generic exceptions, timeouts) and non-retryable (`OperationError` with FAILED state, `HandlerError` with non-retryable type). The Nexus machinery automatically retries the first kind until your `schedule_to_close_timeout` runs out or the circuit breaker opens.

Cancellation is a property of the caller workflow's lifecycle, not something you wire up explicitly in the handler. As long as the operation is async (workflow-backed), cancellation propagates correctly. Sync operations cannot be cancelled because they hold no operation token.

The circuit breaker is per `(caller-Namespace, Endpoint)` pair. A misbehaving handler stops blocking fan-out across the whole caller namespace once the breaker opens, which protects the platform from cascading failure.

## Stop here

Stop both workers (Ctrl-C) when finished. The starter cleans up its own workflows at the end of each scenario, so no extra cleanup is needed: Scenarios B and D `terminate()` (the Nexus operations there are blocked on retries / circuit breaker, so graceful cancellation would stall the demo); Scenario C uses `cancel()` to demonstrate cancellation propagating through the Nexus boundary, and both the payment and compliance workflows end in `Canceled` because the workflow does not catch the cancellation.
