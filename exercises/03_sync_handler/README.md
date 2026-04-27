# Chapter 3: Sync Handler and Worker Wiring

In this chapter, you will implement synchronous Nexus handlers for both operations on the contract and register the handler with a Compliance worker. The Nexus endpoint already exists from Chapter 2.

A sync Nexus operation must complete within 10 seconds. That is enough time for `check_compliance` to call the rule-based checker directly and return. `submit_review` will be a `NotImplementedError` stub for now: it needs a running workflow to send an Update to, and we have not introduced ComplianceWorkflow yet. Chapter 5 introduces the workflow, and Chapter 6 fills `submit_review` in.

By the end of this chapter, you will:

- Implement `check_compliance` as a sync handler that calls `ComplianceChecker` directly
- Stub `submit_review` so the worker starts cleanly
- Register the Nexus service handler on a new Compliance worker

Make your changes in `exercise/`. Look for `TODO 2` and `TODO 3` comments in the code. If you get stuck, compare with `solution/`.

## Part A: Implement the sync handlers (TODO 2)

Open `compliance/service_handler.py`. Three changes:

1. Add the service handler decorator above the class:

   ```python
   @nexusrpc.handler.service_handler(service=ComplianceNexusService)
   ```

2. Decorate both methods with `@nexusrpc.handler.sync_operation`. Replace the `return None` body in `check_compliance` with a call to the rule-based checker:

   ```python
   return _check_compliance(input)
   ```

3. Replace the `return None` body in `submit_review` with the stub raise:

   ```python
   raise NotImplementedError(
       "submit_review needs a workflow to send Updates to (the workflow is introduced in Ch 5; submit_review is implemented in Ch 6)"
   )
   ```

Both methods need the decorator, even the stub. Without it the worker will refuse to start.

## Part B: Register the handler on the Compliance worker (TODO 3)

Open `compliance/worker.py`. Uncomment the registration line inside the `Worker(...)` call:

```python
nexus_service_handlers=[ComplianceNexusServiceHandler()],
```

This worker only registers a Nexus handler. It does not register a workflow or an activity. Chapter 5 will add those alongside the async path.

The worker polls the `compliance-risk` task queue. That name has to match the `--target-task-queue` on the Nexus endpoint, which you created in Chapter 2 (Part C). If you skipped Chapter 2, follow that part now to create the namespaces and the endpoint, then come back here.

## Part C: Run the Compliance worker

From `exercises/03_sync_handler/exercise/`:

```bash
uv run python -m compliance.worker
```

The startup banner should say `Registered: ComplianceNexusServiceHandler (sync only)`. If the worker exits with a Nexus configuration error, check that you decorated both methods on the handler class.

In a second terminal, also run the monolith Payments worker so transactions still process end-to-end (the Payments side does not switch to Nexus until Chapter 4):

```bash
uv run python -m payments.worker
```

In a third terminal:

```bash
uv run python -m payments.starter
```

The transactions still run through the Payments worker's local activity, exactly like Chapter 1. The Compliance worker is up, but nothing calls it yet. That happens in Chapter 4.

## Take Aways

The handler is an ordinary Python class with a decorator. The worker registers it the same way you would register a workflow or activity.

Nothing happens at the Nexus boundary in this chapter, because the Payments workflow still calls `check_compliance` as a local activity. Chapter 4 swaps that call to use the endpoint that Chapter 2 created.

## Stop here

Stop both workers (Ctrl-C) before moving to Chapter 4.
