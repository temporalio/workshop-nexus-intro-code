# Chapter 4: Calling Nexus from a Caller Workflow

In this chapter, you will replace the local compliance activity call inside `PaymentProcessingWorkflow` with a Nexus operation call that routes to the Compliance worker. You will also clean up the Payments worker so it no longer registers `check_compliance` as a local activity.

The Payments side now calls Nexus instead of an activity. The Compliance side still uses the synchronous handler from Chapter 3. The contract has not changed.

By the end of this chapter, you will:

- Replace the activity call with `workflow.create_nexus_client` and `nexus_client.execute_operation`
- Remove `check_compliance` from the Payments worker's `activities` list
- Run the system end-to-end with two workers in two namespaces, connected by Nexus
- See `NexusOperationScheduled` and `NexusOperationCompleted` events in the caller's Event History

Make your changes in `exercise/`. Look for `TODO 4` and `TODO 5` comments in the code. If you get stuck, compare with `solution/`.

## Part A: Swap the activity call for a Nexus call (TODO 4)

Open `payments/workflows.py`. Find the `# TODO 4` comment block in `PaymentProcessingWorkflow`. Delete the activity call below it:

```python
compliance: ComplianceResult = await workflow.execute_activity(
    check_compliance,
    comp_req,
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy=RetryPolicy(...),
)
```

Replace it with the Nexus call:

```python
nexus_client = workflow.create_nexus_client(
    service=ComplianceNexusService,
    endpoint=NEXUS_ENDPOINT,
)
compliance: ComplianceResult = await nexus_client.execute_operation(
    ComplianceNexusService.check_compliance,
    comp_req,
    schedule_to_close_timeout=timedelta(minutes=10),
)
```

Same input. Same output. The workflow is now decoupled from the Compliance team's implementation. You will also need to remove the `check_compliance` import at the top of the file (it is no longer referenced). The Nexus call has no `retry_policy` parameter: Nexus uses a built-in retry policy on the caller side and the call cannot be customized that way. Inside an async (workflow-backed) handler, the underlying workflow's activities and child workflows are the things you tune retries on.

## Part B: Clean up the Payments worker (TODO 5)

Open `payments/worker.py`. Find the `# TODO 5` comment. Two cleanups:

1. Remove `check_compliance` from the `activities` list. The compliance check no longer runs on this worker.
2. Remove the `from compliance.activities import check_compliance` import at the top.

The list should end up as:

```python
activities=[validate_payment, execute_payment],
```

## Part C: Run the system end-to-end

You need three terminals, all from `exercises/04_caller_swap/exercise/`.

**Terminal 1, Compliance worker:**

```bash
uv run python -m compliance.worker
```

Wait for the "Registered: ComplianceNexusServiceHandler (sync only)" banner.

**Terminal 2, Payments worker:**

```bash
uv run python -m payments.worker
```

The banner now says "Nexus: ComplianceNexusService -> compliance-endpoint" and the activities list no longer contains `check_compliance`.

**Terminal 3, run the transactions:**

```bash
uv run python -m payments.starter
```

Expected results:

- TXN-A: COMPLETED, LOW risk
- TXN-B: COMPLETED, MEDIUM risk with the AML monitoring note (the rule-based checker auto-approves MEDIUM in this chapter, the human-in-the-loop path arrives in Chapter 6)
- TXN-C: DECLINED_COMPLIANCE, HIGH risk

## Part D: Inspect the Event History

Open http://localhost:8233. Look at one of the `payment-TXN-*` workflows in the `payments-namespace`. The compliance check now appears as a pair of Nexus events:

- `NexusOperationScheduled`
- `NexusOperationCompleted`

That is the synchronous Nexus operation lifecycle: two events on the caller's history. Notice there is no `ActivityTaskScheduled` event for compliance anymore, that work happens in a different namespace now.

Switch to the `compliance-namespace`. There are no workflows there, because the sync handler does not start one. Chapter 5 changes that.

## Take Aways

A one-line caller change moves work across a namespace boundary durably. Temporal handles routing, retries, and result delivery. The two teams now have separate workers, separate task queues, and separate deployment lifecycles.

The Compliance team currently can only auto-approve or auto-deny. Chapter 5 introduces the workflow-backed compliance check (so Compliance now has a durable workflow per transaction); Chapter 6 layers the Update-driven human review pattern that supports MEDIUM-risk transactions properly.

## Stop here

Stop both workers (Ctrl-C) before moving to Chapter 5.
