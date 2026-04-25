package shared.nexus;

import compliance.domain.ComplianceRequest;
import compliance.domain.ComplianceResult;
import io.nexusrpc.Operation;
import io.nexusrpc.Service;
import shared.domain.ReviewRequest;

/**
 * Nexus Service Interface - the shared contract between Payments and Compliance teams.
 *
 * Operation names use snake_case explicitly so the Java handler interoperates with
 * Python callers (which produce snake_case operation names by default).
 */
@Service
public interface ComplianceNexusService {

    @Operation(name = "check_compliance")
    ComplianceResult checkCompliance(ComplianceRequest request);

    @Operation(name = "submit_review")
    ComplianceResult submitReview(ReviewRequest request);
}
