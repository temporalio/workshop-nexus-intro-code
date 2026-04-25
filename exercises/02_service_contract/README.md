# Chapter 2: Define the Nexus Service Contract

In this chapter, you will define the shared Nexus service contract between the Payments and Compliance teams. The contract is a Python class decorated with `@nexusrpc.service` that names the operations and types their inputs and outputs. Both teams import this class: Payments creates a stub from it, Compliance implements a handler for it.

By the end of this chapter, you will:

- Add the `@nexusrpc.service` decorator to `ComplianceNexusService`
- Type both operations (`check_compliance` and `submit_review`) with `nexusrpc.Operation`
- Confirm the class compiles and the contract is well-formed

Make your changes in `exercise/`. Look for `TODO 1` comments in the code. If you get stuck, compare with `solution/`.

## Part A: Open the contract file

From `exercises/02_service_contract/exercise/`, open `shared/nexus_service.py` in your editor. The class `ComplianceNexusService` has comments showing the template you need to apply.

## Part B: Apply TODO 1

Three changes:

1. Add `@nexusrpc.service` above the `class ComplianceNexusService:` line.
2. Replace the commented-out `check_compliance` line with the typed annotation:

   ```python
   check_compliance: nexusrpc.Operation[ComplianceRequest, ComplianceResult]
   ```

3. Replace the commented-out `submit_review` line with the typed annotation:

   ```python
   submit_review: nexusrpc.Operation[ReviewRequest, ComplianceResult]
   ```

You can remove the `pass` line too. The class no longer needs it once the operations are declared.

Both operations belong in the contract from the start. Ch 3 will only implement `check_compliance` for real, and `submit_review` will be a stub until Ch 5 introduces the workflow it talks to.

## Part C: Verify it imports cleanly

```bash
cd exercises/02_service_contract/exercise
uv run python -c "from shared.nexus_service import ComplianceNexusService; print(ComplianceNexusService)"
```

You should see something like `<class 'shared.nexus_service.ComplianceNexusService'>` printed without errors. If you see an import error or a Nexus runtime error, double check the decorator name and the type annotations.

## What you should take away

The contract is ordinary Python. The Nexus runtime reads the type annotations on a `@nexusrpc.service` class to figure out what operations exist and what shape their requests and responses take. This is the only file both teams need to share.

There is nothing to run in this chapter. Move on to Chapter 3 to implement a handler for the contract.
