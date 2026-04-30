import nexusrpc

from compliance.models import ComplianceRequest, ComplianceResult
from shared.models import ReviewRequest

# TODO 1a: Decorate the class so it counts as a Nexus Service contract.
class ComplianceNexusService:
    """Nexus Service Interface - the shared contract between Payments and Compliance teams.

    Both teams depend on this interface:
      - Payments team creates a nexus client from it (in the workflow)
      - Compliance team implements a handler for it (in the worker)
    """

    # TODO 1b: Declare the check_compliance Operation with its typed input and output.
    # TODO 1c: Declare the submit_review Operation with its typed input and output.
    pass
