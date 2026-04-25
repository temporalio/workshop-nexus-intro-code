# Chapter 5: Async Operations and Updates

In this chapter, you will introduce the workflow-backed compliance check. The Nexus operation `check_compliance` becomes asynchronous: it starts a `ComplianceWorkflow` that runs the rule-based check, sleeps to demonstrate durability, and for MEDIUM-risk transactions waits for a human reviewer's decision. The reviewer submits the decision through `submit_review`, which becomes a real sync handler that uses the Temporal Client to send a Workflow Update.

This is the most substantial chapter in the workshop. You will touch four existing files, create two new ones, and configure a full set of timeouts on the caller side.

By the end of this chapter, you will:

- Implement `check_compliance` as an async Nexus operation backed by a workflow (`@nexus.workflow_run_operation`)
- Create `ComplianceWorkflow` with a `@workflow.update` method for human review
- Replace the `submit_review` `NotImplementedError` stub with a real sync handler that sends an Update
- Add `ReviewCallerWorkflow` on the Payments side and a `review_starter.py` script
- Configure `schedule_to_close_timeout`, `schedule_to_start_timeout`, and `start_to_close_timeout` on the caller's Nexus call
- See three Nexus events in the caller's Event History (`Scheduled`, `Started`, `Completed`) instead of two

Make your changes in `exercise/`. Compare with `solution/` if you get stuck. There are no inline TODO numbers in this chapter, the work is sequenced as Parts below.

## Part A: Create ComplianceWorkflow

Create a new file `compliance/temporal/workflows.py` with the workflow definition. The workflow:

- Runs `check_compliance` as an activity to get an automated risk classification
- Sleeps 10 seconds (this is for the durability demo, kill the worker mid-sleep to see Temporal pick up where it left off)
- Returns immediately for LOW or HIGH risk
- For MEDIUM risk, waits for a `review` Update to provide a human decision

Use the version in `solution/compliance/temporal/workflows.py` as the reference. Key decorators:

```python
@workflow.defn
class ComplianceWorkflow:
    @workflow.run
    async def run(self, request: ComplianceRequest) -> ComplianceResult: ...

    @workflow.update
    async def review(self, approved: bool, explanation: str) -> ComplianceResult: ...

    @review.validator
    def validate_review(self, approved: bool, explanation: str) -> None: ...
```

The validator rejects review attempts that arrive before the workflow is waiting (no auto-result yet) or after a decision was already made. This is what makes the Update idempotent and safe.

## Part B: Convert check_compliance to async

Open `compliance/temporal/nexus_handler.py`. Replace the `check_compliance` body. Currently it is a sync handler that calls the checker directly. Make it an async handler that starts `ComplianceWorkflow`:

```python
@nexus.workflow_run_operation
async def check_compliance(
    self, ctx: nexus.WorkflowRunOperationContext, input: ComplianceRequest
) -> nexus.WorkflowHandle[ComplianceResult]:
    return await ctx.start_workflow(
        ComplianceWorkflow.run,
        input,
        id=f"compliance-{input.transaction_id}",
    )
```

You will need to import `ComplianceWorkflow` from `compliance.temporal.workflows` and add `from temporalio import nexus` at the top.

The decorator change matters. `@nexus.workflow_run_operation` returns a `WorkflowHandle`. The Nexus machinery records a `NexusOperationStarted` event on the caller's history when the workflow begins, and a `NexusOperationCompleted` event when the workflow finishes. The operation can run for up to 60 days.

## Part C: Implement submit_review for real

Stay in `compliance/temporal/nexus_handler.py`. Replace the `NotImplementedError` body in `submit_review` with a real sync handler that sends an Update:

```python
@nexusrpc.handler.sync_operation
async def submit_review(
    self, ctx: nexusrpc.handler.StartOperationContext, input: ReviewRequest
) -> ComplianceResult:
    client = nexus.client()
    handle: WorkflowHandle = client.get_workflow_handle_for(
        ComplianceWorkflow.run,
        workflow_id=f"compliance-{input.transaction_id}",
    )
    return await handle.execute_update(
        ComplianceWorkflow.review,
        args=[input.approved, input.explanation],
    )
```

`nexus.client()` returns the Temporal Client the worker was initialized with. The handler looks up the running ComplianceWorkflow by ID and sends a Workflow Update. The Update returns the same `ComplianceResult` the workflow's `review` method returns, and the Nexus operation forwards it to the caller.

## Part D: Update the Compliance worker

Open `compliance/temporal/worker.py`. The worker currently registers only the Nexus handler. Add the workflow and activity:

```python
worker = Worker(
    client,
    task_queue=TASK_QUEUE,
    workflows=[ComplianceWorkflow],
    activities=[check_compliance],
    activity_executor=executor,
    nexus_service_handlers=[ComplianceNexusServiceHandler()],
)
```

You will also need to import `ComplianceWorkflow` and `check_compliance`, and bring back the `concurrent.futures.ThreadPoolExecutor` block. The `solution/` version shows the full file.

## Part E: Add ReviewCallerWorkflow on the Payments side

Open `payments/temporal/workflows.py`. Add a second workflow class at the bottom of the file that submits a review through Nexus:

```python
@workflow.defn
class ReviewCallerWorkflow:
    @workflow.run
    async def submit_review(self, request: ReviewRequest) -> ComplianceResult:
        nexus_client = workflow.create_nexus_client(
            service=ComplianceNexusService,
            endpoint=NEXUS_ENDPOINT,
        )
        return await nexus_client.execute_operation(
            ComplianceNexusService.submit_review,
            request,
            schedule_to_close_timeout=timedelta(seconds=10),
        )
```

You will also need to import `ReviewRequest` from `shared.domain`.

This workflow exists so the reviewer experience is symmetric with the rest of the system: humans trigger workflows, not raw Update calls. The Nexus call goes through the same endpoint as the compliance check.

## Part F: Add the three timeouts to the compliance Nexus call

Stay in `payments/temporal/workflows.py`. Find the existing `nexus_client.execute_operation` call inside `PaymentProcessingWorkflow`. It currently sets only `schedule_to_close_timeout`. Add two more:

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

- `schedule_to_close_timeout`: the total budget from the moment the operation is scheduled until it must complete. Bounds the worst case across retries.
- `schedule_to_start_timeout`: how long you are willing to wait for the handler to pick up the operation. Useful for tripping early if no Compliance worker is healthy.
- `start_to_close_timeout`: once the handler workflow has started, how long you are willing to wait for it to finish. For workflow-backed async operations this is bounded by the handler workflow's own progress.

## Part G: Update the Payments worker

Open `payments/temporal/worker.py`. Add `ReviewCallerWorkflow` to the workflows list:

```python
workflows=[PaymentProcessingWorkflow, ReviewCallerWorkflow],
```

You will also need to import it from `payments.temporal.workflows`.

## Part H: Add the review starter script

Create a new file `payments/temporal/review_starter.py`. It connects to Temporal, builds a `ReviewRequest`, and executes a `ReviewCallerWorkflow` to approve TXN-B. Use `solution/payments/temporal/review_starter.py` as the reference, the contents are about 50 lines.

## Part I: Run the system end-to-end

You need four terminals, all from `exercises/05_async_operations/exercise/`.

**Terminal 1, Compliance worker:**

```bash
uv run python -m compliance.temporal.worker
```

The banner now says "Registered: ComplianceWorkflow, check_compliance, ComplianceNexusServiceHandler".

**Terminal 2, Payments worker:**

```bash
uv run python -m payments.temporal.worker
```

The banner says "Registered: PaymentProcessingWorkflow, ReviewCallerWorkflow".

**Terminal 3, run the transactions:**

```bash
uv run python -m payments.temporal.starter
```

TXN-A completes immediately as LOW risk. TXN-B blocks: it triggers a workflow on the Compliance side that has classified the risk as MEDIUM and is now waiting for human review. The starter hangs because TXN-B's workflow has not finished.

**Terminal 4, submit the review for TXN-B:**

```bash
uv run python -m payments.temporal.review_starter
```

Watch Terminal 3. As soon as the review is submitted, TXN-B finishes (COMPLETED with MEDIUM risk and the reviewer's explanation), then TXN-C runs and gets DECLINED_COMPLIANCE.

## Part J: Inspect the Event History

Open http://localhost:8233 and look at `payment-TXN-B` in the `payments-namespace`. The compliance Nexus operation now shows three events instead of two:

- `NexusOperationScheduled`
- `NexusOperationStarted`
- `NexusOperationCompleted`

`NexusOperationStarted` is the marker for an async operation. The handler returned a workflow handle, and Temporal recorded that the operation has begun. Look at the timing between `Started` and `Completed`, that is the duration the handler workflow ran, including the time spent waiting for the human review.

In the `compliance-namespace`, `compliance-TXN-B` shows the `WorkflowExecutionUpdateAccepted` and `WorkflowExecutionUpdateCompleted` events for the `review` Update.

## Part K: Optional, durability test

While TXN-B is waiting for review (after Terminal 3 starts but before Terminal 4 submits), kill the Compliance worker in Terminal 1 with Ctrl-C. Wait a few seconds. Restart it with the same command. Then submit the review in Terminal 4.

The review still gets through. The handler workflow resumes from where it stopped, processes the Update, and the Payment workflow completes. This is durability across the Nexus boundary.

## What you should take away

`@nexus.workflow_run_operation` is the bridge between Nexus and Temporal's durability story. Long-running work, human review, retries, and crash recovery all become properties of the underlying workflow rather than concerns the caller has to handle.

The three timeouts give the caller bounded waiting at each stage of the operation lifecycle: how long to wait for a worker to pick it up, how long to wait once it has started, and how long the whole operation can run.

## Stop here

Stop both workers (Ctrl-C) before moving to Chapter 6.
