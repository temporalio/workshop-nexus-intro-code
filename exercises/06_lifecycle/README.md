# Chapter 6: Lifecycle Control: Cancellation, Errors, Circuit Breaker

In this chapter, you will exercise the production-readiness behaviors of Nexus operations: cancelling an in-flight async operation, returning retryable vs non-retryable errors from a handler, and watching the circuit breaker trip after a string of failures.

The compliance handler from Ch 5 already accepts normal transactions. For Ch 6, you will add three failure-injection branches at the top of `check_compliance`. Special `transaction_id` prefixes that the lifecycle starter sends will trigger each scenario. Cancellation needs no handler changes; it propagates automatically from a cancelled caller workflow.

By the end of this chapter, you will:

- Raise `nexusrpc.OperationError` (non-retryable) and observe `NexusOperationFailed` with no retries
- Raise `nexusrpc.HandlerError` with type `INTERNAL` (retryable) and observe Pending Operations in the `BackingOff` state with attempt count climbing
- Cancel an in-flight async Nexus operation from the caller side and watch the cancellation propagate to the underlying `ComplianceWorkflow`
- Trip the Nexus circuit breaker by sending several retryable failures in succession and observe `State: Blocked` with `BlockedReason: The circuit breaker is open`

Make your changes in `exercise/`. Look for `TODO 11` in `compliance/temporal/nexus_handler.py`. If you get stuck, compare with `solution/`.

## Part A: Add the failure-injection branches (TODO 11)

Open `compliance/temporal/nexus_handler.py`. Inside `check_compliance`, before the `start_workflow` call, add three branches:

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

You also need to import `nexusrpc` at the top of the file. The existing `import nexusrpc.handler` does not bring in the top-level error classes.

The branches are mutually exclusive with the normal `start_workflow` path. A normal transaction (TXN-A, TXN-B, TXN-C) hits none of the prefixes and runs as before.

## Part B: Run the lifecycle starter

`payments/temporal/lifecycle_starter.py` is provided. It runs four scenarios in order:

- **Scenario A** sends `TXN-FAIL-NONRETRY-1` and waits for the immediate failure.
- **Scenario B** sends `TXN-FAIL-RETRY-1`, lets it retry for ~20 seconds, then cancels it so the demo can move on.
- **Scenario C** sends `TXN-CANCEL-1` (a normal LOW-risk transaction), waits 3 seconds, then cancels the payment workflow. Cancellation propagates through the Nexus operation to the underlying `ComplianceWorkflow`.
- **Scenario D** sends six `TXN-CIRCUIT-*` transactions back to back, then cancels them all after the breaker trips.

You need both workers running first. Three terminals from `exercises/06_lifecycle/exercise/`:

**Terminal 1, Compliance worker:**

```bash
uv run python -m compliance.temporal.worker
```

**Terminal 2, Payments worker:**

```bash
uv run python -m payments.temporal.worker
```

**Terminal 3, lifecycle starter:**

```bash
uv run python -m payments.temporal.lifecycle_starter
```

The starter runs all four scenarios in sequence (about 90 seconds end to end). Watch the output and watch the Web UI at http://localhost:8233 to follow each scenario.

## Part C: Inspect each scenario in the UI and CLI

### Scenario A: non-retryable error

In the `payments-namespace`, `payment-TXN-FAIL-NONRETRY-1` should be in `Failed` state. Its Event History shows `NexusOperationScheduled` followed by `NexusOperationFailed` with no retries in between. The starter prints the `NexusOperationError` cause that the caller surfaces.

### Scenario B: retryable error with BackingOff

While the starter is in this scenario (~20 seconds), run:

```bash
temporal workflow describe -w payment-TXN-FAIL-RETRY-1 -n payments-namespace
```

You should see `Pending Nexus Operations` with `State: BackingOff` and `Attempt` increasing on each subsequent describe call. After ~20 seconds, the starter cancels the workflow so we can move on.

### Scenario C: cancellation propagation

After the starter ends Scenario C, look at both sides:

```bash
temporal workflow describe -w payment-TXN-CANCEL-1   -n payments-namespace
temporal workflow describe -w compliance-TXN-CANCEL-1 -n compliance-namespace
```

The payment workflow ends as `CancelRequested`/`Canceled`. The Nexus operation in the caller's history shows a `NexusOperationCanceled` event. The handler `ComplianceWorkflow` (in the compliance namespace) is also cancelled, even though we never told it directly. Cancellation flows through the Nexus boundary.

If you want to control how the caller waits for the cancellation, the available cancellation types on `nexus_client.execute_operation` are `ABANDON`, `TRY_CANCEL`, `WAIT_REQUESTED`, and `WAIT_COMPLETED`. The default is `WAIT_COMPLETED`. The lifecycle starter uses the default; experiment with the others to feel the trade-offs.

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

The breaker stays open for ~60 seconds, then enters half-open and probes with a single request. If that request succeeds, the breaker closes again. The starter cancels all six workflows at the end so they do not keep retrying.

## What you should take away

Nexus errors split into two categories on the wire: retryable (`HandlerError` with retryable type, generic exceptions, timeouts) and non-retryable (`OperationError` with FAILED state, `HandlerError` with non-retryable type). The Nexus machinery automatically retries the first kind until your `schedule_to_close_timeout` runs out or the circuit breaker opens.

Cancellation is a property of the caller workflow's lifecycle, not something you wire up explicitly in the handler. As long as the operation is async (workflow-backed), cancellation propagates correctly. Sync operations cannot be cancelled because they hold no operation token.

The circuit breaker is per `(caller-Namespace, Endpoint)` pair. A misbehaving handler stops blocking fan-out across the whole caller namespace once the breaker opens, which protects the platform from cascading failure.

## Stop here

Stop both workers (Ctrl-C) when finished. The starter cancels its own workflows at the end of each scenario, so no extra cleanup is needed.
