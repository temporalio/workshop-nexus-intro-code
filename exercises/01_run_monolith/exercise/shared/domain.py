from dataclasses import dataclass


@dataclass
class ReviewRequest:
    """Request data for submitting a human review decision via Nexus.

    Used by the ReviewCallerWorkflow to call the submitReview Nexus operation.
    The Compliance team's sync Nexus handler receives this and sends a Workflow
    Update to the running ComplianceWorkflow.
    """

    transaction_id: str = ""
    approved: bool = False
    explanation: str = ""
