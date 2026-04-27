# Chapter 2: Define the Nexus Service Contract

In this chapter, you will define the shared Nexus Service contract between the Payments and Compliance teams, and stand up the runtime infrastructure that will route calls across the team boundary: a separate namespace per team, plus a Nexus Endpoint that points callers at the Compliance team's task queue.

There are two distinct artifacts:

- The **contract** is a Python class decorated with `@nexusrpc.service` that names the operations and types their inputs and outputs. It lives in `shared/service.py` and is imported by both teams: Payments creates a stub from it (Ch 4), Compliance implements a handler for it (Ch 3). The Temporal server has no awareness of this class; it exists only at runtime in each worker.
- The **Endpoint** is a routing rule in Temporal's Nexus registry. It carries the target namespace and task queue, plus a Markdown description that documents what the contract exposes. The Endpoint description is the only Nexus thing that shows up in the Web UI.

By the end of this chapter, you will:

- Add the `@nexusrpc.service` decorator to `ComplianceNexusService` and type both operations
- Create the `payments-namespace` and `compliance-namespace` namespaces
- Create the `compliance-endpoint` Nexus Endpoint with a Markdown description that documents the contract
- Find the Endpoint in the Web UI and read the description there

Make your changes in `exercise/`. Look for `TODO 1` comments in the code. If you get stuck, compare with `solution/`.

## Part A: Apply TODO 1

Open `exercise/shared/service.py`. The class `ComplianceNexusService` has comments showing the template you need to apply. Three changes:

1. Add `@nexusrpc.service` above the `class ComplianceNexusService:` line.
2. Replace the commented-out `check_compliance` line with the typed annotation:

   ```python
   check_compliance: nexusrpc.Operation[ComplianceRequest, ComplianceResult]
   ```

3. Replace the commented-out `submit_review` line with the typed annotation:

   ```python
   submit_review: nexusrpc.Operation[ReviewRequest, ComplianceResult]
   ```

You can remove the `pass` line. The class no longer needs it once the operations are declared.

Both operations belong in the contract from the start. Ch 3 will only implement `check_compliance` for real, and `submit_review` will be a stub until Ch 6 turns it into a real Update sender.

If you forget the `@nexusrpc.service` decorator the file still loads. The class is just an undecorated Python class with no Nexus metadata. Nothing complains until a worker tries to register a handler against it (Ch 3) or a caller workflow tries to build a stub from it (Ch 4), at which point you get a confusing failure deep in worker startup. Catching the mistake here saves debugging later: the line above the class must be `@nexusrpc.service`, and both operation lines must use the `nexusrpc.Operation[Input, Output]` annotation form (no `=`, no body).

## Part B: Create the namespaces

The Payments and Compliance teams will live in separate namespaces from Ch 3 onward. Each namespace is its own isolated execution environment with separate workflows, separate task queues, and separate access control. Nexus is the only thing that crosses the boundary.

From any directory:

```bash
temporal operator namespace create --namespace payments-namespace
temporal operator namespace create --namespace compliance-namespace
```

Verify both exist:

```bash
temporal operator namespace list
```

You should see `payments-namespace` and `compliance-namespace` alongside `default`.

## Part C: Create the Nexus Endpoint

A Nexus Endpoint is a routing rule in Temporal's Nexus registry. It tells the server: when a caller invokes the Endpoint named `compliance-endpoint`, deliver the request to a worker polling the `compliance-risk` task queue in `compliance-namespace`. Callers reference the Endpoint by name; they do not need to know the target namespace or task queue.

The Endpoint also carries a Markdown description that documents the contract for anyone browsing the registry. We ship one at the repo root in `compliance-endpoint.md`. 

From the repo root:

```bash
temporal operator nexus endpoint create \
  --name compliance-endpoint \
  --target-namespace compliance-namespace \
  --target-task-queue compliance-risk \
  --description-file compliance-endpoint.md
```

Confirm the Endpoint exists and the description was attached:

```bash
temporal operator nexus endpoint list
temporal operator nexus endpoint get --name compliance-endpoint
```

The `get` output should include the Markdown description from `compliance-endpoint.md` under the `Description` field.

## Part D: Find the Endpoint in the Web UI

The Web UI exposes the Nexus registry under the **Nexus Endpoints** view. Open http://localhost:8233 and click **Nexus Endpoints** in the left-hand navigation (or browse directly to http://localhost:8233/nexus/endpoints).

You should see a single Endpoint row, `compliance-endpoint`, targeting `compliance-namespace` / `compliance-risk`. Click into it and you will see the description rendered as Markdown, the same content as `compliance-endpoint.md`. This page is what an engineer on a different team would look at to understand what the Endpoint exposes before writing a caller workflow against it.

The Endpoint exists at the cluster level. It is not scoped to any one namespace. That is what lets it bridge teams.

## Take Aways

The contract is ordinary Python. The Nexus runtime reads the type annotations on a `@nexusrpc.service` class to figure out what operations exist and what shape their requests and responses take. The contract has no UI surface; it lives only in the Python files both teams import.

The Endpoint is the matching server-side artifact: a named routing rule that points callers at the team-and-task-queue serving the contract, plus a description that documents what the contract does. The description is what shows up in the Web UI. Together they let the Payments team write `nexus_client.execute_operation(ComplianceNexusService.check_compliance, ...)` (Ch 4) without ever knowing, or being able to break, anything about how Compliance implements the handler.

There is no worker to run in this chapter. Move on to Chapter 3 to implement a handler for the contract.
