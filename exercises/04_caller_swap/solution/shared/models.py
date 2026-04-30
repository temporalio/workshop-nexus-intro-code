from dataclasses import dataclass

@dataclass
class ReviewRequest:
    """A human reviewer's decision on a transaction.

    Used by the submit_review Nexus operation. Ch 3 declares it on the contract;
    Ch 6 wires it up to a real Update sender.
    """

    transaction_id: str
    approved: bool
    explanation: str
