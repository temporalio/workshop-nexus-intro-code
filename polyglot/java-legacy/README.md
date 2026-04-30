# Polyglot: Java Compliance Worker

Java compliance worker used as the polyglot connector demo at the end of the **Introduction to Temporal Nexus** workshop. It is functionally equivalent to the Chapter 6 Python compliance handler (workflow-backed `check_compliance` plus the human-review path) and registers against the same `compliance-namespace` and `compliance-risk` task queue, so the Python `payments` worker calls it through the existing Nexus endpoint with no Python-side change.

## Prerequisites

- Java 11 or later
- Maven 3.6 or later
- A running Temporal dev server, the `payments-namespace` and `compliance-namespace`, and the `compliance-endpoint` Nexus endpoint. See the workshop's [root README](../../README.md) and the Chapter 2 README for the one-time setup.
- **The Python compliance worker must be stopped before you start this one.** Workers from different SDKs cannot safely share a workflow task queue: workflow histories produced by different SDKs are not interchangeable, so only one of the two compliance workers may poll `compliance-risk` at a time.

## Build and run

From this directory:

```bash
mvn compile
mvn -q exec:java
```

`exec:java` runs the default main class declared in `pom.xml`, which is `compliance.temporal.ComplianceWorkerApp`. The worker connects to `compliance-namespace` and polls `compliance-risk`. Expected log line:

```
Compliance Worker started on: compliance-risk
```

## Demo flow

The demo runs against a Python caller from Chapter 5, 6, or 7. Chapter 7's solution state is the recommended target because its caller has the timeouts and `ReviewCallerWorkflow` registered. From a Chapter 7 `solution/` directory:

1. Confirm no Python compliance worker is running.
2. Start the Java worker as above.
3. Confirm it is the only poller on `compliance-risk`:
   ```bash
   temporal task-queue describe --task-queue compliance-risk -n compliance-namespace
   ```
4. Start the Python payments worker and the starter:
   ```bash
   uv run python -m payments.worker
   uv run python -m payments.starter
   ```
5. Watch the Web UI. Each `payment-TXN-*` workflow in `payments-namespace` shows the same three Nexus events (`Scheduled`, `Started`, `Completed`) as a pure-Python run; the corresponding `compliance-TXN-*` workflows in `compliance-namespace` are now Java workflows.

For MEDIUM-risk transactions (TXN-B), submit a review with the Python `review_starter` — the Java workflow has the same `review` Update and `validateReview` validator the Python Ch 6 workflow has:

```bash
uv run python -m payments.review_starter
```

> **Use `payments.starter`, not `payments.lifecycle_starter`.** The Java handler does not implement the Ch 7 failure-injection branches (`TXN-FAIL-NONRETRY`, `TXN-FAIL-RETRY`, `TXN-CIRCUIT`), so those scenarios silently succeed against the Java worker instead of demonstrating the lifecycle behaviors. The lifecycle scenarios are out of scope for the polyglot demo.

## How Java interoperates with the Python contract

The Java service interface uses explicit annotations to align with Python's snake_case wire format:

- `@Operation(name = "check_compliance")` and `@Operation(name = "submit_review")` on `shared/nexus/ComplianceNexusService.java` make the operation names match what Python sends. Without the explicit names, Java defaults to camelCase method names (`checkCompliance`) and Python's calls fail with `NOT_FOUND: Unrecognized operation`.
- `@JsonProperty("snake_case_name")` on each field, getter, and constructor argument in the data classes (`compliance/domain/`, `shared/domain/`) makes the JSON wire format match Python's dataclass serialization.
- A `@JsonCreator(mode = JsonCreator.Mode.PROPERTIES)` constructor with `@JsonProperty` parameters lets Jackson construct the object from the JSON keys directly. The default no-arg constructor stays in place for the SDK's other code paths.

These annotations are the polyglot tax: when one side speaks snake_case and the other speaks camelCase, one side needs explicit overrides. We chose Java so the Python contract stays idiomatic.

## Stopping

Ctrl-C in the terminal running `mvn exec:java`. After stopping, restart the Python compliance worker if you want to continue the workshop in pure-Python mode.
