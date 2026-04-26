import nexusrpc

from compliance.models import ComplianceRequest, ComplianceResult
from shared.models import ReviewRequest

@nexusrpc.service
class ComplianceNexusService:
    """Nexus Service Interface - the shared contract between Payments and Compliance teams.

    Both teams depend on this interface:
      - Payments team creates a nexus client from it (in the workflow)
      - Compliance team implements a handler for it (in the worker)
    """

    check_compliance: nexusrpc.Operation[ComplianceRequest, ComplianceResult]
    submit_review: nexusrpc.Operation[ReviewRequest, ComplianceResult]
