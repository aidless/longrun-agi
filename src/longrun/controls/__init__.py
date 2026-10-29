"""Deterministic evidence gates for small research claims."""

from .claim_gate import (
    ClaimGateResult,
    ClaimSchemaCase,
    EvidenceClaimGate,
    generate_claim_schema_cases,
    run_claim_schema_probe,
)
from .confounding import (
    ConfoundingCase,
    ConfoundingCheck,
    audit_confounding_control_suite,
    check_confounding,
    generate_confounding_control_cases,
    run_confounding_control_probe,
)
from .evidence import (
    EvidenceGate,
    EvidenceRecord,
    GateResult,
    SubgroupResult,
    audit_control_suite,
)

__all__ = [
    "ConfoundingCase",
    "ConfoundingCheck",
    "ClaimGateResult",
    "ClaimSchemaCase",
    "EvidenceGate",
    "EvidenceClaimGate",
    "EvidenceRecord",
    "GateResult",
    "SubgroupResult",
    "audit_confounding_control_suite",
    "audit_control_suite",
    "check_confounding",
    "generate_claim_schema_cases",
    "generate_confounding_control_cases",
    "run_claim_schema_probe",
    "run_confounding_control_probe",
]
