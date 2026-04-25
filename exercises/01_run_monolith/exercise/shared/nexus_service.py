# ===================================================================
#  TODO 1: Define the Nexus service interface (the shared contract)
# ===================================================================
#
# This is the shared contract between teams - like an OpenAPI spec, but durable.
# Both teams depend on this class:
#   - Payments team creates a nexus client from it (in the workflow)
#   - Compliance team implements a handler for it (in the worker)
#
# What to add for TODO 1:
#
#   1. Add @nexusrpc.service decorator to the class
#   2. Add nexusrpc.Operation type annotations to BOTH operations
#
#   The Nexus runtime validates all operations in a @nexusrpc.service class
#   at worker startup. Every operation must be typed - or the worker will fail.
#
# Template:
#
#   @nexusrpc.service
#   class ComplianceNexusService:
#       check_compliance: nexusrpc.Operation[ComplianceRequest, ComplianceResult]
#       submit_review: nexusrpc.Operation[ReviewRequest, ComplianceResult]
#
# Both operations are part of the contract, even though Chapter 3 will only
# implement check_compliance for real. submit_review will be a stub until
# Chapter 5 adds the workflow-backed compliance check.

import nexusrpc

from compliance.domain import ComplianceRequest, ComplianceResult
from shared.domain import ReviewRequest


# TODO 1: Add @nexusrpc.service decorator
class ComplianceNexusService:
    """Nexus Service Interface - the shared contract between Payments and Compliance teams.

    Both teams depend on this interface:
      - Payments team creates a nexus client from it (in the workflow)
      - Compliance team implements a handler for it (in the worker)
    """

    # TODO 1: Add nexusrpc.Operation type annotation for check_compliance
    # check_compliance: nexusrpc.Operation[ComplianceRequest, ComplianceResult]

    # TODO 1: Add nexusrpc.Operation type annotation for submit_review
    # submit_review: nexusrpc.Operation[ReviewRequest, ComplianceResult]

    pass
