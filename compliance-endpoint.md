# Compliance Endpoint

Cross-team Nexus endpoint for the Payments team to invoke compliance checks.
The Python contract lives in `shared/service.py` and is shared between
the calling team (Payments) and the implementing team (Compliance).

The handler may be implemented in any Temporal SDK that supports Nexus.
Today it ships in two flavors that share the same wire contract:

- **Python** - `compliance/service_handler.py` in each chapter's
  `solution/`. From Chapter 5 onward the handler is workflow-backed;
  Chapter 6 adds human-in-the-loop review for MEDIUM-risk transactions.
- **Java (polyglot)** - `polyglot/java-legacy/src/main/java/compliance/temporal/`.
  Drop-in replacement; the Python caller hits it through this same endpoint
  with no Python-side code change.

## Operations

### `check_compliance`

Run an automated compliance check on a payment transaction.

- **Input** - `ComplianceRequest`
  - `transaction_id: str`
  - `amount: float`
  - `sender_country: str`
  - `receiver_country: str`
  - `description: str`
- **Output** - `ComplianceResult`
  - `transaction_id: str`
  - `approved: bool`
  - `risk_level: "LOW" | "MEDIUM" | "HIGH"`
  - `explanation: str`
- **Mode** - synchronous in Ch 3; asynchronous (workflow-backed) in Ch 5+.
  In the async form the handler starts a `compliance-{transaction_id}`
  workflow on the `compliance-risk` task queue and runs the rule-based
  check as an activity. From Ch 6 onward, MEDIUM-risk transactions wait
  on a `review` Update from a human reviewer.

### `submit_review`

Submit a human reviewer's approve/deny decision for a MEDIUM-risk
transaction whose `compliance-{transaction_id}` workflow is awaiting review.

- **Input** - `ReviewRequest`
  - `transaction_id: str`
  - `approved: bool`
  - `explanation: str`
- **Output** - `ComplianceResult` (the resolved decision returned by the
  workflow's update handler)
- **Mode** - synchronous. Must complete within the 10-second Nexus
  sync-handler deadline. Internally the handler uses the worker's Temporal
  client to send a Workflow Update to the running compliance workflow.

## Routing

- Target namespace: `compliance-namespace`
- Target task queue: `compliance-risk`

## Owner

Compliance team.
