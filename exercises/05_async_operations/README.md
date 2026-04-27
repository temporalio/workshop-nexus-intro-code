# Chapter 5: Async (Workflow-Backed) Nexus Operations

In this chapter, you will convert the compliance check from a synchronous Nexus handler to a **workflow-backed** asynchronous one. Instead of returning a result inline within the 10-second sync deadline, the handler starts a `ComplianceWorkflow` and returns a handle to it. The Nexus runtime turns that handle into the three-event Nexus pattern (`Scheduled`, `Started`, `Completed`) on the caller's history.

The MEDIUM-risk human-in-the-loop review path is **not** in this chapter, but arrives in Chapter 6. After Ch 5, all three transactions still resolve automatically (LOW completes, MEDIUM auto-approves with the AML monitoring note, HIGH declines), but the Compliance side is now durable: a workflow runs there, and you can kill the Compliance worker mid-flight and watch the work resume on restart.

By the end of this chapter, you will:

- Implement `ComplianceWorkflow.run` as a workflow that runs the rule-based `check_compliance` activity
- Convert the `check_compliance` Nexus handler from `@nexusrpc.handler.sync_operation` to `@nexus.workflow_run_operation`
- Register the new workflow + activity on the Compliance worker
- Configure `schedule_to_start_timeout` and `start_to_close_timeout` on the caller's Nexus call (the `schedule_to_close_timeout` was already set in Ch 4)
- See three Nexus events in the caller's Event History (`Scheduled`, `Started`, `Completed`) instead of two

Make your changes in `exercise/`. Look for `TODO 6` through `TODO 9` in the code. If you get stuck, compare with `solution/`.

## Part A: Implement ComplianceWorkflow.run (TODO 6)

Open `compliance/workflows.py`. The skeleton has the class structure, the `run` signature, and a `NotImplementedError` placeholder. Replace the placeholder body with the activity call:

```python
self._auto_result = await workflow.execute_activity(
    check_compliance,
    request,
    start_to_close_timeout=timedelta(seconds=30),
)
return self._auto_result
```

We store the result on `self._auto_result` (rather than a local) so Chapter 6 can extend this method with a MEDIUM-risk wait_condition without restructuring it.

## Part B: Convert check_compliance to async (TODO 7)

Open `compliance/service_handler.py`. The current implementation is the Ch 3/4 sync handler that calls the rule-based check directly. Replace it with a `workflow_run_operation`:

```python
@nexus.workflow_run_operation
async def check_compliance(
    self, ctx: nexus.WorkflowRunOperationContext, input: ComplianceRequest
) -> nexus.WorkflowHandle[ComplianceResult]:
    return await ctx.start_workflow(
        ComplianceWorkflow.run,
        input,
        id=f"compliance-{input.transaction_id}",
        id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
    )
```

Three pieces matter here:

1. The decorator changes from `@nexusrpc.handler.sync_operation` to `@nexus.workflow_run_operation`.
2. The context type changes to `nexus.WorkflowRunOperationContext`, and the return type to `nexus.WorkflowHandle[ComplianceResult]`.
3. `id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING` makes the handler idempotent on retry: if the Nexus start request is retried for the same transaction, the handler returns a handle to the already-running workflow instead of failing with `WorkflowAlreadyStartedError`.

`submit_review` stays a `NotImplementedError` stub. Ch 6 turns it into a real Update sender.

## Part C: Register the workflow + activity on the Compliance worker (TODO 8)

Open `compliance/worker.py`. The Ch 3/4 worker only registered the Nexus handler. Now that the handler starts a workflow and that workflow runs an activity, register both:

```python
with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ComplianceWorkflow],
        activities=[check_compliance],
        activity_executor=executor,
        nexus_service_handlers=[ComplianceNexusServiceHandler()],
    )
```

The activity is registered as a plain `def` in `compliance/activities.py` (no `async`), so the worker needs an `activity_executor` to run it on a thread. We use a `ThreadPoolExecutor` here, the same pattern the Payments worker uses for its sync activities.

## Part D: Add the missing timeouts on the caller (TODO 9)

Open `payments/workflows.py`. The Ch 4 caller set only `schedule_to_close_timeout`. Now that the operation can run for minutes (the handler workflow runs an activity, may sleep, etc.), add bounds for each lifecycle phase:

```python
compliance: ComplianceResult = await nexus_client.execute_operation(
    ComplianceNexusService.check_compliance,
    comp_req,
    schedule_to_close_timeout=timedelta(minutes=10),
    schedule_to_start_timeout=timedelta(minutes=1),
    start_to_close_timeout=timedelta(minutes=8),
)
```

What each timeout means:

- `schedule_to_close_timeout` - total budget from the moment the operation is scheduled until it must complete. Bounds the worst case across retries.
- `schedule_to_start_timeout` - how long you are willing to wait for the handler to pick up the operation. Trips early if no Compliance worker is healthy.
- `start_to_close_timeout` - once the handler workflow has started, how long the operation may run before the caller treats it as timed out.

## Part E: Run the system end-to-end

Three terminals from `exercises/05_async_operations/exercise/`.

**Terminal 1, Compliance worker:**

```bash
uv run python -m compliance.worker
```

The banner now says `Registered: ComplianceWorkflow, check_compliance, ComplianceNexusServiceHandler`.

**Terminal 2, Payments worker:**

```bash
uv run python -m payments.worker
```

**Terminal 3, run the transactions:**

```bash
uv run python -m payments.starter
```

All three transactions complete or decline automatically:

- TXN-A: COMPLETED, LOW risk
- TXN-B: COMPLETED, MEDIUM risk with the AML monitoring note (auto-approved by the rule-based check; Ch 6 adds the human-in-the-loop pause)
- TXN-C: DECLINED_COMPLIANCE, HIGH risk

## Part F: Inspect the Event History

Open http://localhost:8233 and look at one of the `payment-TXN-*` workflows in the `payments-namespace`. The compliance Nexus operation now shows **three events** instead of two:

- `NexusOperationScheduled`
- `NexusOperationStarted`
- `NexusOperationCompleted`

`NexusOperationStarted` is the marker for an async operation: the handler returned a workflow handle, and Temporal recorded that the handler workflow has begun. The duration between `Started` and `Completed` is the handler workflow's runtime.

Switch to `compliance-namespace`. There is now a `compliance-TXN-*` workflow per transaction - the `ComplianceWorkflow` that the Nexus handler started.

## Part G: Optional - durability test

While `payments.starter` is running, kill the Compliance worker (Ctrl-C in Terminal 1) right when one of the `compliance-TXN-*` workflows is mid-activity. Wait a few seconds. Restart it with the same command. The handler workflow resumes from where it stopped, the activity completes, the Nexus operation reports `Completed`, and the payment workflow finishes. Durability of the handler workflow is now a property of the Nexus boundary itself - the caller doesn't have to do anything special to get crash recovery.

## Take Aways

`@nexus.workflow_run_operation` is the bridge between Nexus and Temporal's durability story. The handler workflow can run for up to 60 days, which is dramatically more than the 10-second sync deadline. Crash recovery, retries, and result delivery all become properties of the handler workflow rather than concerns the caller has to handle.

The three timeouts give the caller bounded waiting at each stage of the operation lifecycle, which becomes operationally important once operations can run for minutes or hours.

## Stop here

Stop both workers (Ctrl-C) before moving to Chapter 6.
