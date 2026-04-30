# Chapter 6: Updates Through Nexus (Human-in-the-Loop)

In this chapter, you will layer human-in-the-loop review on top of the workflow-backed handler from Ch 5. `ComplianceWorkflow` gains a `review` Workflow Update that a reviewer can call to approve or deny a MEDIUM-risk transaction. The Update is reachable through Nexus: a `submit_review` sync handler on the compliance side resolves the right workflow ID and forwards the call as `handle.execute_update(...)`.

The pattern is general: any Workflow Update on the handler side is callable from any caller workflow over Nexus, by way of a tiny sync Nexus operation that does the lookup and the `execute_update`.

By the end of this chapter, you will:

- Add a `@workflow.update review` (and its validator) to `ComplianceWorkflow`, plus the MEDIUM-risk `sleep` + `wait_condition` branch
- Replace the `submit_review` `NotImplementedError` stub with a real sync handler that sends a Workflow Update
- Add `ReviewCallerWorkflow` on the Payments side and register it with the Payments worker
- Use the supplied `payments/review_starter.py` to trigger the review flow
- Watch a MEDIUM-risk transaction (TXN-B) block until you submit a review

Make your changes in `exercise/`. Look for `TODO 10` through `TODO 12` in the code. The review starter (`payments/review_starter.py`) is provided in full so the chapter can focus on the new concepts: the validator, the Update sender, and the caller workflow. If you get stuck, compare with `solution/`.

## Part A: Add the review path to ComplianceWorkflow (TODO 10)

Open `compliance/workflows.py`. Three additions:

1. **State**, in `__init__`:

   ```python
   self._review_result: ComplianceResult | None = None
   ```

2. **Branch the run method on risk_level.** LOW and HIGH return immediately as before; MEDIUM sleeps then waits for the review Update:

   ```python
   if self._auto_result.risk_level != "MEDIUM":
       return self._auto_result

   await workflow.sleep(timedelta(seconds=10))
   await workflow.wait_condition(lambda: self._review_result is not None)
   assert self._review_result is not None  # wait_condition guarantees this
   return self._review_result
   ```

   The sleep is for the durability demo (Part F below). The `wait_condition` is the durable pause that the Update will resolve.

3. **The Update handler + validator:**

   ```python
   @workflow.update
   async def review(self, approved: bool, explanation: str) -> ComplianceResult:
       self._review_result = ComplianceResult(
           transaction_id=self._request.transaction_id,
           approved=approved,
           risk_level="MEDIUM",
           explanation=explanation,
       )
       return self._review_result

   @review.validator
   def validate_review(self, approved: bool, explanation: str) -> None:
       if self._auto_result is None or self._auto_result.risk_level != "MEDIUM":
           raise ValueError("Workflow is not awaiting review")
       if self._review_result is not None:
           raise ValueError("Review already submitted")
   ```

   The validator rejects review attempts that arrive before the workflow is waiting (no auto-result yet) or after a decision was already made. This is what makes the Update idempotent and safe.

## Part B: Implement submit_review for real (TODO 11)

Open `compliance/service_handler.py`. Replace the `NotImplementedError` body in `submit_review` with a real sync handler that sends an Update:

```python
client = nexus.client()
handle: WorkflowHandle = client.get_workflow_handle_for(
    ComplianceWorkflow.run,
    workflow_id=f"compliance-ch06-{input.transaction_id}",
)
return await handle.execute_update(
    ComplianceWorkflow.review,
    args=[input.approved, input.explanation],
)
```

You also need to import `WorkflowHandle`:

```python
from temporalio.client import WorkflowHandle
```

`nexus.client()` returns the Temporal Client the worker was initialized with. The handler resolves the running ComplianceWorkflow by ID and sends a Workflow Update. `execute_update` returns the same `ComplianceResult` the workflow's `review` method returns, and the Nexus operation forwards it to the caller.

## Part C: Add ReviewCallerWorkflow (TODO 12)

Two file edits.

**`payments/workflows.py`:** add `ReviewRequest` to the `imports_passed_through` block, then add a second workflow class at the bottom of the file:

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

This workflow exists so the reviewer experience is symmetric with the rest of the system: humans trigger workflows, not raw Update calls. The Nexus call goes through the same endpoint as the compliance check.

**`payments/worker.py`:** register the new workflow:

```python
from payments.workflows import PaymentProcessingWorkflow, ReviewCallerWorkflow
...
workflows=[PaymentProcessingWorkflow, ReviewCallerWorkflow],
```

## Part D: Run the system end-to-end

Four terminals from `exercises/06_updates/exercise/`.

**Terminal 1, Compliance worker:**

```bash
uv run python -m compliance.worker
```

**Terminal 2, Payments worker:**

```bash
uv run python -m payments.worker
```

The banner now lists `PaymentProcessingWorkflow, ReviewCallerWorkflow`.

**Terminal 3, run the transactions:**

```bash
uv run python -m payments.starter
```

TXN-A completes quickly as LOW risk. TXN-B **blocks**: it triggered a `compliance-ch06-TXN-B` workflow that classified the risk as MEDIUM, slept for 10 seconds, and is now waiting for human review. The starter is sitting on its `execute_workflow` call for TXN-B.

**Terminal 4, submit the review for TXN-B:**

```bash
uv run python -m payments.review_starter
```

Watch Terminal 3. As soon as the review is submitted, TXN-B finishes (COMPLETED with MEDIUM risk and the reviewer's explanation), then TXN-C runs and gets DECLINED_COMPLIANCE.

## Part E: Inspect the Event History

Open http://localhost:8233 and look at `payment-ch06-TXN-B` in the `payments-namespace`. The compliance Nexus operation still shows three events (`Scheduled`, `Started`, `Completed`), but the duration between `Started` and `Completed` is much longer - that is the time spent waiting for human review.

In `compliance-namespace`, `compliance-ch06-TXN-B` shows `WorkflowExecutionUpdateAccepted` and `WorkflowExecutionUpdateCompleted` events for the `review` Update. That is the Update propagating through Nexus from the Payments side.

## Part F: Optional - durability test

While TXN-B is waiting for review (after Terminal 3 starts but before Terminal 4 submits), kill the Compliance worker in Terminal 1 with Ctrl-C. Wait a few seconds. Restart it with the same command. Then submit the review in Terminal 4.

The review still gets through. The handler workflow resumes from where it stopped, processes the Update, and the Payment workflow completes. This is durability across the Nexus boundary: the compliance side can crash and recover without the payments side noticing.

## A note on Workflow ID design

Both payment and compliance workflows in this chapter use a chapter-prefixed, business-meaningful ID — `payment-ch06-TXN-B` and `compliance-ch06-TXN-B`. The `ch06-` prefix exists purely to prevent cross-chapter contamination: all chapters run the same three transaction IDs (TXN-A, TXN-B, TXN-C) in the same namespaces, so without a prefix a stuck `payment-TXN-B` from this chapter would block the same ID in the next chapter.

No random suffix is added. Temporal's best practice is to use stable, business-meaningful workflow IDs because they act as idempotency keys: if the starter is retried for the same transaction, the running or completed workflow is found by ID rather than a duplicate being created. The `review_starter.py` is the one exception — its `ReviewCallerWorkflow` is a short-lived trigger that you may run multiple times for the same TXN-B, so it appends a UUID to avoid `WorkflowAlreadyStartedError` on repeat runs.

The `submit_review` handler depends on this stability: it constructs `compliance-ch06-{input.transaction_id}` from the transaction ID in the `ReviewRequest` to look up the running `ComplianceWorkflow`. A random suffix would make that lookup impossible.

**Re-running this chapter:** because IDs are stable, running `payments.starter` a second time while TXN-B is still blocked will return a `WorkflowAlreadyStartedError`. Either submit the review first, or restart the dev server for a clean namespace before re-running.

## Take Aways

Workflow Updates ride through Nexus the same way `workflow_run_operation` results do - the `submit_review` sync handler is just a thin wrapper that does the lookup and forwards the Update. The validator on the handler workflow is the safety belt that keeps Updates from arriving early or twice.

Together with `workflow_run_operation`, this gives you the full async / human-in-the-loop pattern over a typed contract that crosses team boundaries cleanly.

## Stop here

Stop both workers (Ctrl-C) before moving to Chapter 7.
