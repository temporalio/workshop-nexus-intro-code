# Chapter 1: Run the Monolith

In this chapter, you will run the existing monolithic payment system and observe how the Payments and Compliance teams' code share a single worker, a single namespace, and therefore a single blast radius. There are no code changes in this chapter. The goal is to feel the problem that Nexus solves before changing anything.

By the end of this chapter, you will:

- Run the Payments worker that hosts both Payments and Compliance code today
- Start three transactions that exercise LOW, MEDIUM, and HIGH risk paths
- See in the Web UI that everything runs in the `payments-namespace` against a single task queue

There are no TODOs to fill in. Use the `exercise/` directory.

## Prerequisites

Make sure the one-time setup in the repo root README is done: `uv sync` from the root, and `temporal server start-dev` running in its own terminal. You also need both namespaces and the Nexus endpoint created (the endpoint is created here so future chapters can route to it without re-running setup).

```bash
temporal operator namespace create --namespace payments-namespace
temporal operator namespace create --namespace compliance-namespace

temporal operator nexus endpoint create \
  --name compliance-endpoint \
  --target-namespace compliance-namespace \
  --target-task-queue compliance-risk
```

## Part A: Start the Payments worker

From `exercises/01_run_monolith/exercise/`:

```bash
uv run python -m payments.temporal.worker
```

Read the startup banner. Notice the worker registers `PaymentProcessingWorkflow` and three activities, including `check_compliance`. Compliance code runs on this worker today.

## Part B: Run three transactions

In a second terminal, from the same directory:

```bash
uv run python -m payments.temporal.starter
```

Three payment workflows run in sequence: TXN-A, TXN-B, TXN-C. Watch the worker logs and the starter output.

## Part C: Inspect the Web UI

Open http://localhost:8233 and select the `payments-namespace`. You should see three workflow executions:

- `payment-TXN-A`: COMPLETED with LOW risk
- `payment-TXN-B`: COMPLETED with MEDIUM risk and an AML monitoring note
- `payment-TXN-C`: DECLINED_COMPLIANCE with HIGH risk

Click into one of them and look at the Event History. You will see the compliance check appear as an `ActivityTaskScheduled` event, just like any other activity. There is no separation between Payments code and Compliance code.

Switch to the `compliance-namespace`. It is empty. Compliance code is not running there yet.

## What you should take away

The monolith works. It is also fragile in the ways the lecture covered: a misbehaving compliance change can stop payments, and the Compliance team has no way to ship code independently. The next chapter starts the decoupling by introducing the shared service contract.

## Stop here

Press Ctrl-C in the worker terminal before moving to Chapter 2.
