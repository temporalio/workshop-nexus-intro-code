from temporalio import activity

from compliance.compliance_checker import check_compliance as _check_compliance
from compliance.domain import ComplianceRequest, ComplianceResult


@activity.defn
def check_compliance(request: ComplianceRequest) -> ComplianceResult:
    """Run automated compliance check. Delegates to the rule-based ComplianceChecker."""
    return _check_compliance(request)
