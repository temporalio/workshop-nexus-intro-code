import nexusrpc

from compliance.models import ComplianceRequest, ComplianceResult
from shared.models import ReviewRequest

# TODO 1 (Chapter 2, Part A): Add @nexusrpc.service decorator and Operation type annotations.
class ComplianceNexusService:
    """Nexus Service Interface - the shared contract between Payments and Compliance teams.

    Both teams depend on this interface:
      - Payments team creates a nexus client from it (in the workflow)
      - Compliance team implements a handler for it (in the worker)
    """

    pass
