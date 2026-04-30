# Topology Sandbox

`game/index.html` is a single-file browser sandbox that visualizes the workshop's Chapter 5+ topology: a Payments worker, a Nexus endpoint, and a Compliance worker, with synthetic payments flowing through. No dependencies, no server, no real Temporal cluster. Open the file in a browser and it runs.

By the end of this sandbox, you will:

- See the resilient end-state of the system you are about to build
- Stop and start each service and watch in-flight workflows pause, not fail
- Notice that the `Lost` counter never increments, no matter what you stop

This is the self-paced companion to the Instruqt prologue. The day-of workshop runs the same visualizer with a guided talk track; this README is for picking it up on your own.

## Prerequisites

A modern browser. Nothing else. The visualizer does not connect to Temporal, does not require Python, and does not need anything from the rest of this repo.

## Part A: Open it

From the repo root:

```bash
open game/index.html        # macOS
xdg-open game/index.html    # Linux
```

You should see four panes:

- **Topology** (top-left): three services, each with a Stop / Start button.
- **Score**: cumulative counters for completed, declined, in-flight, blocked, and lost transactions.
- **Workflows In Flight**: each row is one synthetic payment moving through three steps (validate, compliance check, execute).
- **Event History** (right): the same event names the real Temporal Web UI uses.

Synthetic payments spawn automatically every couple of seconds. Let it run untouched for a few seconds so the Workflows In Flight pane builds up a healthy backlog before you start clicking.

## Part B: Stop the Compliance Worker

Click **Stop** on the Compliance Worker box (right side of the topology). Watch what happens to the workflows in flight:

- Any payment at the compliance step turns yellow ("blocked"). It does not turn red. It does not fail.
- New payments still spawn and run through the validate step. They pile up at compliance.
- The `Lost` counter does not move.

Click **Start**. The blocked payments turn back to blue and resume from where they were, not from the beginning.

## Part C: Stop the Nexus Endpoint

Click **Stop** on the Nexus Endpoint box (the middle one). Same shape: in-flight payments at the compliance step turn yellow, the `Lost` counter stays at 0, new payments queue up. Click **Start** and they flow again.

Try the same with the Payments Worker. The pause-not-fail behavior is the same; the difference is which step blocks. A Payments Worker outage blocks at validate (step 1) or execute (step 3); a Compliance Worker outage blocks at compliance (step 2); a Nexus Endpoint outage blocks the cross-team call between them.

## Take Aways

The visualizer is a fake, but the property it depicts is real. Every Stop button you click here represents an outage you would otherwise be paged for in production: a worker crash, a network partition, a deploy that did not come back. In none of those cases does an in-flight workflow lose work. It pauses, and resumes when its dependency is back.

That property is the load-bearing reason the rest of the workshop is worth the work. The labels on the boxes (`Nexus Endpoint`, `compliance-endpoint`, `NexusOperationScheduled`) get defined as you progress through the chapters. The shape of what you are looking at, three services bound by a typed contract that survives outages, is the destination.

When you are ready, start with `exercises/01_run_monolith/` and go pull apart a monolith.
