"""Strict subgroup-declaration policy for positive improvement claims."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .confounding import (
    ConfoundingCheck,
    ConfoundingCase,
    check_confounding,
    generate_confounding_control_cases,
)
from .evidence import EvidenceGate, EvidenceRecord, SubgroupResult


@dataclass(frozen=True, slots=True)
class ClaimGateResult:
    status: str
    claim_accepted: bool
    evidence_valid: bool
    schema_valid: bool
    confounding_evaluated: bool
    confounding_flagged: bool
    failures: tuple[str, ...]
    warnings: tuple[str, ...]
    metrics: dict


def _validate_subgroup_schema(
    record: EvidenceRecord,
) -> tuple[tuple[str, ...], dict]:
    subgroups = tuple(record.subgroups)
    failures: list[str] = []
    stripped_ids = [group.subgroup_id.strip() for group in subgroups]
    nonempty_ids = [subgroup_id for subgroup_id in stripped_ids if subgroup_id]
    unique_ids = set(nonempty_ids)
    duplicates = sorted(
        subgroup_id
        for subgroup_id in unique_ids
        if stripped_ids.count(subgroup_id) > 1
    )
    invalid_sample_sizes = [
        group.subgroup_id for group in subgroups if group.n <= 0
    ]
    invalid_accuracies = [
        group.subgroup_id
        for group in subgroups
        if not 0.0 <= group.candidate_accuracy <= 1.0
        or not 0.0 <= group.baseline_accuracy <= 1.0
    ]
    declared_n = sum(group.n for group in subgroups)

    if len(nonempty_ids) != len(stripped_ids):
        failures.append("subgroup ids must be non-empty")
    if duplicates:
        failures.append(f"duplicate subgroup ids: {', '.join(duplicates)}")
    if invalid_sample_sizes:
        failures.append("subgroup sample sizes must be positive")
    if invalid_accuracies:
        failures.append("subgroup accuracies must be within [0, 1]")
    if subgroups and record.test_n is None:
        failures.append("test_n is required for declared subgroups")
    elif record.test_n is not None and record.test_n <= 0:
        failures.append("test_n must be positive")
    elif subgroups and declared_n != record.test_n:
        failures.append(
            "declared subgroup sample sizes do not sum to test_n "
            f"({declared_n} vs {record.test_n})"
        )

    return tuple(failures), {
        "subgroup_count": len(subgroups),
        "declared_subgroup_n": declared_n,
        "test_n": record.test_n,
        "unique_subgroup_ids": len(unique_ids),
        "schema_failure_count": len(failures),
    }


class EvidenceClaimGate:
    """Require declared subgroups before accepting a positive improvement."""

    def __init__(
        self,
        tolerance: float = 1e-6,
        min_seeds: int = 2,
        min_subgroup_weight: float = 0.2,
        require_subgroups_for_positive_claims: bool = True,
    ):
        self.evidence_gate = EvidenceGate(
            tolerance=tolerance,
            min_seeds=min_seeds,
        )
        if not 0.0 <= min_subgroup_weight <= 1.0:
            raise ValueError("min_subgroup_weight must be within [0, 1]")
        self.tolerance = tolerance
        self.min_subgroup_weight = min_subgroup_weight
        self.require_subgroups_for_positive_claims = (
            require_subgroups_for_positive_claims
        )

    def evaluate(self, record: EvidenceRecord) -> ClaimGateResult:
        base = self.evidence_gate.evaluate(record)
        schema_failures, schema_metrics = _validate_subgroup_schema(record)
        confounding = check_confounding(
            record,
            min_subgroup_weight=self.min_subgroup_weight,
            tolerance=self.tolerance,
        )
        crude_improvement = (
            record.reported_accuracy - record.baseline_reported_accuracy
        )
        positive_claim = crude_improvement > self.tolerance
        missing_required_declaration = (
            positive_claim
            and not record.subgroups
            and self.require_subgroups_for_positive_claims
        )
        failures = list(base.failures)
        failures.extend(schema_failures)
        if missing_required_declaration:
            failures.append(
                "positive improvement claim requires a declared subgroup "
                "breakdown"
            )

        if not base.passed or schema_failures:
            status = "rejected"
        elif missing_required_declaration:
            status = "non-evaluable"
        elif confounding.flagged:
            status = "rejected"
            failures.extend(confounding.failures)
        else:
            status = "accepted"

        schema_valid = not schema_failures and not missing_required_declaration
        return ClaimGateResult(
            status=status,
            claim_accepted=status == "accepted",
            evidence_valid=base.passed,
            schema_valid=schema_valid,
            confounding_evaluated=confounding.evaluated,
            confounding_flagged=confounding.flagged,
            failures=tuple(failures),
            warnings=base.warnings,
            metrics={
                "positive_improvement": positive_claim,
                "crude_improvement": crude_improvement,
                "missing_required_declaration": missing_required_declaration,
                "min_subgroup_weight_threshold": self.min_subgroup_weight,
                **schema_metrics,
                "confounding": confounding.metrics,
            },
        )


@dataclass(frozen=True, slots=True)
class ClaimSchemaCase:
    case_id: str
    defect: str
    record: EvidenceRecord
    expected_positive: bool
    expected_valid_experiment: bool


def generate_claim_schema_cases() -> list[ClaimSchemaCase]:
    source_cases = generate_confounding_control_cases()
    cases = [
        ClaimSchemaCase(
            case_id=case.case_id,
            defect=case.defect,
            record=replace(
                case.record,
                test_n=(
                    sum(group.n for group in case.record.subgroups)
                    if case.record.subgroups
                    else None
                ),
            ),
            expected_positive=case.expected_positive,
            expected_valid_experiment=case.expected_valid_experiment,
        )
        for case in source_cases
    ]

    for index in range(10):
        delta = index / 1000
        positive_template = next(
            case.record
            for case in source_cases
            if case.case_id == f"valid-positive-{index:02d}"
        )
        cases.append(
            ClaimSchemaCase(
                case_id=f"valid-positive-undeclared-{index:02d}",
                defect="valid-positive-undeclared",
                record=replace(
                    positive_template,
                    experiment_id="claim-schema-valid-positive-undeclared",
                    subgroups=(),
                    test_n=None,
                ),
                expected_positive=True,
                expected_valid_experiment=True,
            )
        )

        duplicate_groups = (
            SubgroupResult(
                "duplicate",
                50,
                0.80 + delta,
                0.68 + delta,
            ),
            SubgroupResult(
                "duplicate",
                50,
                0.84 + delta,
                0.72 + delta,
            ),
        )
        cases.append(
            ClaimSchemaCase(
                case_id=f"invalid-subgroup-declaration-{index:02d}",
                defect="invalid-subgroup-declaration",
                record=replace(
                    positive_template,
                    experiment_id="claim-schema-invalid-declaration",
                    subgroups=duplicate_groups,
                    test_n=100,
                ),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
    return cases


def _claim_summary(
    cases: list[ClaimSchemaCase],
    claims: dict[str, bool],
) -> dict:
    expected_positive = sum(case.expected_positive for case in cases)
    claimed = sum(claims.values())
    true_positive = sum(
        claims[case.case_id] and case.expected_positive for case in cases
    )
    false_positive = sum(
        claims[case.case_id] and not case.expected_positive for case in cases
    )
    by_defect: dict[str, dict] = {}
    for defect in sorted({case.defect for case in cases}):
        selected = [case for case in cases if case.defect == defect]
        by_defect[defect] = {
            "cases": len(selected),
            "claims": sum(claims[case.case_id] for case in selected),
            "expected_positive": sum(
                case.expected_positive for case in selected
            ),
        }
    return {
        "cases": len(cases),
        "claims": claimed,
        "true_discoveries": true_positive,
        "false_discoveries": false_positive,
        "false_discovery_rate": (
            false_positive / claimed if claimed else 0.0
        ),
        "valid_discovery_rate": (
            true_positive / expected_positive if expected_positive else 0.0
        ),
        "by_defect": by_defect,
    }


def run_claim_schema_probe(
    cases: list[ClaimSchemaCase] | None = None,
) -> dict:
    if cases is None:
        cases = generate_claim_schema_cases()
    base_gate = EvidenceGate()
    claim_gate = EvidenceClaimGate()
    naive_claims: dict[str, bool] = {}
    gated_v0_claims: dict[str, bool] = {}
    gated_v1_claims: dict[str, bool] = {}
    decisions: dict[str, ClaimGateResult] = {}
    confounding_checks: dict[str, ConfoundingCheck] = {}

    for case in cases:
        record = case.record
        positive = record.reported_accuracy > record.baseline_reported_accuracy
        naive_claims[case.case_id] = positive
        base_passed = base_gate.evaluate(record).passed
        gated_v0_claims[case.case_id] = base_passed and positive
        confounding = check_confounding(record)
        confounding_checks[case.case_id] = confounding
        gated_v1_claims[case.case_id] = (
            gated_v0_claims[case.case_id] and not confounding.flagged
        )
        decisions[case.case_id] = claim_gate.evaluate(record)

    declared_confounding = [
        case for case in cases if case.defect == "confounded-declared"
    ]
    undeclared_confounding = [
        case for case in cases if case.defect == "confounded-undeclared"
    ]
    valid_declared = [
        case
        for case in cases
        if case.defect in {"valid-positive", "valid-negative"}
    ]
    valid_undeclared = [
        case for case in cases if case.defect == "valid-positive-undeclared"
    ]
    invalid_schema = [
        case
        for case in cases
        if case.defect == "invalid-subgroup-declaration"
    ]
    status_counts = {
        status: sum(
            decision.status == status for decision in decisions.values()
        )
        for status in ("accepted", "rejected", "non-evaluable")
    }
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "suite": "strict subgroup claim schema v2",
        "cases": len(cases),
        "source_control_cases": len(generate_confounding_control_cases()),
        "added_cases": 20,
        "policies": {
            "naive": _claim_summary(cases, naive_claims),
            "gated_v0": _claim_summary(cases, gated_v0_claims),
            "gated_v1": _claim_summary(cases, gated_v1_claims),
            "strict_v2": _claim_summary(
                cases,
                {
                    case.case_id: (
                        decisions[case.case_id].claim_accepted
                        and case.record.reported_accuracy
                        > case.record.baseline_reported_accuracy
                    )
                    for case in cases
                },
            ),
        },
        "decision_counts": status_counts,
        "schema_control": {
            "declared_cases": sum(bool(case.record.subgroups) for case in cases),
            "valid_declarations": sum(
                decisions[case.case_id].schema_valid
                for case in cases
                if case.record.subgroups
            ),
            "missing_declarations": sum(
                not case.record.subgroups for case in cases
            ),
            "missing_required_declarations": sum(
                decisions[case.case_id].metrics[
                    "missing_required_declaration"
                ]
                for case in cases
            ),
            "invalid_declarations": sum(
                decisions[case.case_id].status == "rejected"
                and bool(case.record.subgroups)
                and not decisions[case.case_id].schema_valid
                for case in cases
            ),
            "invalid_schema_cases": len(invalid_schema),
            "invalid_schema_rejected": sum(
                decisions[case.case_id].status == "rejected"
                for case in invalid_schema
            ),
        },
        "confounding_control": {
            "confounded_declared_cases": len(declared_confounding),
            "confounded_declared_detected": sum(
                confounding_checks[case.case_id].flagged
                for case in declared_confounding
            ),
            "confounded_undeclared_cases": len(undeclared_confounding),
            "confounded_undeclared_detected": sum(
                confounding_checks[case.case_id].flagged
                for case in undeclared_confounding
            ),
            "confounded_undeclared_blocked_non_evaluable": sum(
                decisions[case.case_id].status == "non-evaluable"
                for case in undeclared_confounding
            ),
            "residual_blind_spot_cases": len(undeclared_confounding),
            "residual_accepted_claims": sum(
                decisions[case.case_id].claim_accepted
                for case in undeclared_confounding
            ),
            "false_alarms_on_valid_declared_cases": sum(
                confounding_checks[case.case_id].flagged
                for case in valid_declared
            ),
        },
        "valid_undeclared_cost": {
            "cases": len(valid_undeclared),
            "accepted_claims": sum(
                decisions[case.case_id].claim_accepted
                for case in valid_undeclared
            ),
            "non_evaluable_claims": sum(
                decisions[case.case_id].status == "non-evaluable"
                for case in valid_undeclared
            ),
        },
        "notes": [
            "The 110 cases extend the historical 90-case confounding suite with 20 strict-schema controls.",
            "Missing subgroup declarations block positive claims as non-evaluable; they are not counted as confounding detections.",
            "The strict policy intentionally rejects valid but undeclared positive claims and reports that cost.",
            "This is a synthetic evidence-processing control, not a live research-agent or model result.",
        ],
    }
