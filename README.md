# Workshop Nexus Intro - Code

Code for the **Introduction to Temporal Nexus** workshop (Replay 2026).
Companion repo: [`workshop-nexus-intro`](https://github.com/temporalio/workshop-nexus-intro) (slides, Instruqt lab, course plan).

## What's here

```
workshop-nexus-intro-code/
├── exercises/
│   ├── 01_run_monolith/        Ch 1: Run the monolith and feel the problem
│   ├── 02_service_contract/    Ch 2: Define the Nexus Service contract
│   ├── 03_sync_handler/        Ch 3: Sync handler + Worker wiring + Endpoint
│   ├── 04_caller_swap/         Ch 4: Calling Nexus from a caller Workflow
│   ├── 05_async_operations/    Ch 5: Async (workflow-backed) Nexus operations
│   ├── 06_updates/             Ch 6: Updates through Nexus (human-in-the-loop)
│   └── 07_lifecycle/           Ch 7: Cancellation, errors, circuit breaker
└── polyglot/
    └── java-legacy/            Java compliance worker for the polyglot connector demo
```

Each chapter directory under `exercises/` (from Chapter 2 onward) contains:

- `exercise/` - starting state for the chapter. Attendees fill in the TODOs.
- `solution/` - reference state with the chapter's TODOs completed.

Each chapter's `exercise/` is self-contained: an attendee can `uv sync` and run a single chapter's `exercise/` directory in isolation. In Chapters 2-4, `exercise/` is the previous chapter's `solution/` with new TODO callouts; in Chapters 5-7, `exercise/` may also include skeleton files (e.g. an empty `compliance/workflows.py` with a `NotImplementedError` body) that the chapter's TODOs ask the attendee to fill in.

Chapter 1 has no TODOs (the goal is to run the monolith and observe it), so it ships only a `solution/` directory. Pick up the `exercise/` + `solution/` pattern from Chapter 2 onward.

## Prerequisites

- Python 3.14 or later
- [uv](https://docs.astral.sh/uv/)
- [Temporal CLI](https://docs.temporal.io/cli) v1.3.0 or later

## Running a chapter

Install dependencies once from the repo root:

```bash
uv sync
```

This creates a single `.venv/` at the root that all chapter snapshots share (the dependencies are identical across chapters: `temporalio` and `nexus-rpc`).

From inside any `<chapter>/exercise/` or `<chapter>/solution/` directory:

```bash
uv run python -m payments.worker
uv run python -m compliance.worker
uv run python -m payments.starter
```

`uv run` walks up the directory tree to find the root `pyproject.toml` and uses the root `.venv`. Each chapter's `payments/`, `compliance/`, and `shared/` packages are picked up from the chapter's working directory automatically.

Open one terminal per worker and per starter. See the workshop content repo for chapter-specific run instructions.

### Temporal dev server (one-time, before any chapter)

```bash
temporal server start-dev
```

The Web UI is at http://localhost:8233. The dev server creates a `default` namespace automatically; that is all Chapter 1 needs. The split namespaces (`payments-namespace`, `compliance-namespace`) and the `compliance-endpoint` Nexus endpoint are created interactively in **Chapter 2**, alongside the contract that uses them - see `exercises/02_service_contract/README.md` Parts D and E.

## Polyglot (Java compliance worker)

`polyglot/java-legacy/` is a pre-built Java **compliance** worker used as the polyglot connector demo at the end of the workshop. It contains only the compliance side - the Java equivalent of the Python `compliance/` package, plus the Java `ComplianceNexusService` interface for wire compatibility. The Python `payments` worker, starter, and caller workflows on the Python side are unchanged; the Java handler simply replaces the Python handler at the same Nexus endpoint.

From Chapter 5 onward (where the Python compliance handler is `@nexus.workflow_run_operation`), the Python caller workflow hits this Java handler instead of the Python one. Same Nexus Service contract. Different language. No code change in Python. The Event History on the caller side looks identical to the pure-Python Ch 5/6/7 run - three Nexus events (`Scheduled`, `Started`, `Completed`) - and a `compliance-TXN-*` workflow runs on the Compliance side, just authored in Java.

> The polyglot demo is intended to be run against the **Ch 7 solution state** (its caller has the timeouts and `ReviewCallerWorkflow` registered). It also runs cleanly against Ch 5 and Ch 6. Use `payments.starter` for the demo, not `payments.lifecycle_starter`: the Java handler is the Ch 6 equivalent and does not implement the Ch 7 failure-injection branches (TXN-FAIL-*, TXN-CIRCUIT-*), so those scenarios would silently succeed instead of demonstrating the lifecycle behaviors.

### Prerequisites

- Java 11 or later
- Maven 3.6+
- The Temporal dev server, namespaces, and `compliance-endpoint` from the common Temporal setup above.
- **Stop the Python compliance worker before running the Java one.** Workers from different SDKs cannot safely share a workflow task queue: workflow histories produced by different SDKs are not interchangeable. The Java worker uses the same `compliance-namespace` and `compliance-risk` task queue that the Python compliance worker uses, so only one of them may be running at a time.

### Build and run

From `polyglot/java-legacy/`:

```bash
mvn compile
mvn -q exec:java
```

`exec:java` runs the default main class declared in `pom.xml`, which is `compliance.temporal.ComplianceWorkerApp`. The worker connects to `compliance-namespace` and polls the `compliance-risk` task queue. You should see:

```
Compliance Worker started on: compliance-risk
```

### Demo flow

1. Confirm the Python compliance worker is stopped. Both workers cannot poll the same task queue safely (see Prerequisites above).
2. Start the Java worker as above. Confirm it is the only poller on `compliance-risk` with `temporal task-queue describe --task-queue compliance-risk -n compliance-namespace`.
3. Start the Python payments worker from Ch 5, 6, or 7 (`uv run python -m payments.worker`).
4. Run the Python starter: `uv run python -m payments.starter` from the same chapter directory.
5. Watch the Web UI. The Python `payment-TXN-A` workflow shows the same Nexus event sequence as the pure-Python Ch 5/6/7 run - `Scheduled`, `Started`, `Completed` - but `compliance-TXN-A` in `compliance-namespace` is now a Java workflow.

### How Java interoperates with the Python contract

The Java service contract uses explicit annotations to align with Python's snake_case wire format. See `polyglot/java-legacy/src/main/java/shared/nexus/ComplianceNexusService.java` and the data classes under `compliance/domain/` and `shared/domain/`:

- `@Operation(name = "check_compliance")` and `@Operation(name = "submit_review")` make the Nexus operation names match what Python sends. Without the explicit names, Java defaults to the camelCase Java method names (`checkCompliance`) and Python's calls fail with `NOT_FOUND: Unrecognized operation`.
- `@JsonProperty("snake_case_name")` on each field, getter, and constructor argument makes the JSON wire format match Python's dataclass serialization. Without these, Jackson defaults to camelCase JSON keys and deserialization fails with `UnrecognizedPropertyException`.
- A `@JsonCreator(mode = JsonCreator.Mode.PROPERTIES)` constructor with `@JsonProperty` parameters lets Jackson construct the object from the JSON keys directly. The default no-arg constructor stays in place for the SDK's other code paths.

These annotations are the polyglot tax: when one side speaks snake_case and the other speaks camelCase, one of them needs explicit overrides. We chose Java since the Python contract stays idiomatic.

## Chapters 5 and 6 highlights

Chapter 5 introduces the workflow-backed compliance check. Going from `solution/` of Ch 4 to `solution/` of Ch 5 the learner:

- Converts `check_compliance` from `@nexusrpc.handler.sync_operation` to `@nexus.workflow_run_operation` so it can run for longer than the 10-second sync deadline.
- Adds a new `compliance/workflows.py` containing `ComplianceWorkflow`, which runs the rule-based check as an activity and returns the result.
- Updates the Compliance worker to register `ComplianceWorkflow` and the `check_compliance` activity alongside the Nexus service handler.
- Configures `schedule_to_start_timeout` and `start_to_close_timeout` on the caller's Nexus call to bound how long the operation can wait at each stage of its lifecycle (the `schedule_to_close_timeout` was set in Ch 4).

After Ch 5 all three transactions still resolve automatically: LOW completes, MEDIUM auto-approves with the AML monitoring note, HIGH declines.

Chapter 6 layers human-in-the-loop review on top:

- Adds `@workflow.update review` (and its validator) plus the `sleep` + `wait_condition` MEDIUM-risk branch to `ComplianceWorkflow`.
- Replaces the `submit_review` `NotImplementedError` stub with a real sync handler that uses the Temporal Client to send the review Update to the running `ComplianceWorkflow`.
- Adds `ReviewCallerWorkflow` on the Payments side and a `review_starter.py` that submits review decisions through Nexus.

After Ch 6, MEDIUM-risk TXN-B blocks until a reviewer submits a decision (run `python -m payments.review_starter`). LOW and HIGH transactions still complete or decline automatically.

## Provenance

The Python code under `01_run_monolith/` through `04_caller_swap/` is derived from the [`edu-nexus-code`](https://github.com/temporalio/edu-nexus-code) Python port of the [Decoupling Temporal Services with Nexus tutorial](https://learn.temporal.io/tutorials/nexus/nexus-sync-tutorial-java/), restructured so Ch 3 and Ch 4 use synchronous Nexus operations only. Chapter 5 introduces the workflow-backed async path; Chapter 6 adds the human-in-the-loop Updates that the original tutorial bundled into its single solution. The Java code under `polyglot/java-legacy/` is the Java solution from the same repo.

`07_lifecycle/` adds failure-injection branches to the compliance handler so the included `lifecycle_starter.py` can exercise non-retryable errors, retryable errors with backoff, caller-driven cancellation, and the Nexus circuit breaker.
