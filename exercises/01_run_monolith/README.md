# Chapter 1: Run the Monolith

In this chapter, you will run the existing monolithic payment system and observe what happens when two teams' code is coupled across every available axis: same Python package tree, same worker process, same task queue, same namespace. There are no code changes in this chapter. The goal is to feel the problem that Nexus solves before we start prying the teams apart.

A note on the framing: the workshop's monolith is the *most extreme* form of coupling, where the Compliance team's `check_compliance` is registered as an activity on the Payments team's worker. In real production deployments most teams already separate workers per workflow type, so the most universal version of this problem is "two teams in the same namespace with no contract between them." Nexus is also the canonical fix for that - and for two related anti-patterns it replaces:

- **Child workflows for cross-team calls** - leak the target namespace, task queue, and workflow options to the caller; can't cross namespaces in Temporal Cloud.
- **Activity-wrapped HTTP / RPC** - per-target mTLS, error-mapping boilerplate, no first-class observability or async-result handling.
- **Shared activities in one worker** *(what this chapter demonstrates)* - Compliance must ship code into the Payments worker. No governance, no version skew handling, no isolated blast radius.

We chose the third version for Ch 1 because it's visceral in a way the others aren't: you'll see Compliance code literally importing into the Payments worker process. The lessons transfer to the more realistic same-namespace-different-workers case in Ch 2 onward.

By the end of this chapter, you will:

- Run the Payments worker that hosts both Payments and Compliance code today
- Start three transactions that exercise LOW, MEDIUM, and HIGH risk paths
- See in the Web UI that everything runs in a single namespace (`default`) against a single task queue, with no boundary between Payments and Compliance code

There are no TODOs to fill in, so this chapter ships only a `solution/` directory - the workshop's `exercise/` + `solution/` pattern starts in Chapter 2 once the first TODO appears.

## Prerequisites

Make sure the one-time setup in the repo root README is done: `uv sync` from the root, and `temporal server start-dev` running in its own terminal. The dev server creates the `default` namespace automatically - that is all this chapter needs. The split namespaces (`payments-namespace`, `compliance-namespace`) and the Nexus endpoint come into play in Chapter 2, when we introduce the cross-team contract.

## Part A: Start the Payments worker

From `exercises/01_run_monolith/solution/`:

```bash
uv run python -m payments.worker
```

Read the startup banner. Notice the worker registers `PaymentProcessingWorkflow` and three activities, including `check_compliance`. Compliance code runs on this worker today.

## Part B: Run three transactions

In a second terminal, from the same directory:

```bash
uv run python -m payments.starter
```

Three payment workflows run in sequence: TXN-A, TXN-B, TXN-C. Watch the worker logs and the starter output.

## Part C: Inspect the Web UI

Open http://localhost:8233 (the `default` namespace is selected by default). You should see three workflow executions:

- `payment-TXN-A`: COMPLETED with LOW risk
- `payment-TXN-B`: COMPLETED with MEDIUM risk and an AML monitoring note
- `payment-TXN-C`: DECLINED_COMPLIANCE with HIGH risk

Click into one of them and look at the Event History. You will see the compliance check appear as an `ActivityTaskScheduled` event, just like any other activity. There is no separation between Payments code and Compliance code, and there is no Nexus boundary anywhere - everything runs in this one namespace, on one task queue, in one worker.

## Take Aways

The monolith works. The fragility is in the layers of coupling it accepts:

- **Code coupling.** The Payments worker `import`s Compliance code. The two teams must agree on Python package layout, dependency versions, and release cadence.
- **Process coupling.** Both teams' code runs in the same worker process. A bug in `check_compliance` that crashes the worker also stops `validate_payment` and `execute_payment`.
- **Task-queue coupling.** Both teams' work flows through one queue. Compliance's slow checks compete for the same poller slots as Payments' executions.
- **Namespace coupling.** Workflow IDs, search attributes, RBAC, and visibility queries are all shared. Compliance can list, query, signal, or terminate any Payments workflow they can construct an ID for.
- **Deployment coupling.** One CI/CD pipeline. Compliance can't ship a fix without re-deploying Payments, and vice versa.

In production you usually already have separate worker fleets per workflow type, which removes the process and task-queue coupling. The remaining coupling - same namespace, no contract - is what Nexus most fundamentally addresses. The next chapter introduces the shared service contract that lets the two teams talk through a typed interface instead of through a shared Python package, and stands up the namespace split + Nexus endpoint that the rest of the workshop builds on.

## Stop here

Press Ctrl-C in the worker terminal before moving to Chapter 2.
