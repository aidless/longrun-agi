"""Deterministic subgroup-confounding checks for research claims.

The v0 Evidence Gate checks leakage, baseline integrity, seeding, and metric
reproducibility. It cannot see a confounder, because a v0 record carries no
subgroup breakdown. This module adds an optional stratified control:

- when a record declares subgroups, the weighted subgroup accuracies must
  reproduce the reported aggregate accuracies;
- when the aggregate claims an improvement, every materially weighted
  subgroup must show that improvement as well.

A record that declares no subgroups is *not evaluable*. That is a measured
residual blind spot, not a solved problem.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .evidence import EvidenceGate, EvidenceRecord, SubgroupResult


DEFAULT_MIN_SUBGROUP_WEIGHT = 0.2
DEFAULT_TOLERANCE = 1e-6


@dataclass(frozen=True, slots=True)
class ConfoundingCheck:
    evaluated: bool
    flagged: bool
    failures: tuple[str, ...]
    metrics: dict


def check_confounding(
    record: EvidenceRecord,
    min_subgroup_weight: float = DEFAULT_MIN_SUBGROUP_WEIGHT,
    tolerance: float = DEFAULT_TOLERANCE,
) -> ConfoundingCheck:
    """Check a declared subgroup breakdown for effect heterogeneity."""

    subgroups = tuple(record.subgroups)
    if not subgroups:
        return ConfoundingCheck(
            evaluated=False,
            flagged=False,
            failures=(),
            metrics={
                "reason": "no declared subgroups",
                "subgroup_count": 0,
            },
        )

    total_n = sum(group.n for group in subgroups)
    if total_n <= 0:
        return ConfoundingCheck(
            evaluated=False,
            flagged=False,
            failures=("subgroup sample sizes sum to zero",),
            metrics={
                "reason": "empty subgroup sample sizes",
                "subgroup_count": len(subgroups),
            },
        )

    weighted_candidate = (
        sum(group.n * group.candidate_accuracy for group in subgroups)
        / total_n
    )
    weighted_baseline = (
        sum(group.n * group.baseline_accuracy for group in subgroups)
        / total_n
    )
    crude_improvement = record.reported_accuracy - record.baseline_reported_accuracy

    failures: list[str] = []
    if abs(weighted_candidate - record.reported_accuracy) > tolerance:
        failures.append(
            "subgroup aggregate does not reproduce the reported candidate "
            f"accuracy ({weighted_candidate:.6f} vs {record.reported_accuracy:.6f})"
        )
    if abs(weighted_baseline - record.baseline_reported_accuracy) > tolerance:
        failures.append(
            "subgroup aggregate does not reproduce the reported baseline "
            f"accuracy ({weighted_baseline:.6f} vs "
            f"{record.baseline_reported_accuracy:.6f})"
        )

    worst = min(subgroups, key=lambda group: group.improvement)
    if crude_improvement > tolerance:
        for group in subgroups:
            weight = group.n / total_n
            if weight >= min_subgroup_weight and group.improvement <= tolerance:
                failures.append(
                    "subgroup regression: "
                    f"subgroup '{group.subgroup_id}' has improvement "
                    f"{group.improvement:.6f} at weight {weight:.4f}"
                )

    return ConfoundingCheck(
        evaluated=True,
        flagged=bool(failures),
        failures=tuple(failures),
        metrics={
            "subgroup_count": len(subgroups),
            "total_n": total_n,
            "weighted_candidate_accuracy": weighted_candidate,
            "weighted_baseline_accuracy": weighted_baseline,
            "crude_improvement": crude_improvement,
            "min_subgroup_improvement": worst.improvement,
            "min_subgroup_weight": worst.n / total_n,
            "min_subgroup_weight_threshold": min_subgroup_weight,
        },
    )


def _valid_record(subgroups: tuple[SubgroupResult, ...]) -> EvidenceRecord:
    return EvidenceRecord(
        experiment_id="confounding-control",
        train_ids=frozenset({"tr-1", "tr-2", "tr-3"}),
        test_ids=frozenset({"te-1", "te-2"}),
        feature_names=("f-1", "f-2"),
        target_name="label",
        reported_accuracy=0.82,
        recomputed_accuracy=0.82,
        baseline_reported_accuracy=0.70,
        baseline_recomputed_accuracy=0.70,
        seeds=(0, 1, 2),
        test_set_id="confounding-test-v1",
        subgroups=subgroups,
    )


_CONSISTENT = (
    SubgroupResult("s1", 50, 0.80, 0.68),
    SubgroupResult("s2", 50, 0.84, 0.72),
)
_REGRESSING = (
    SubgroupResult("s1", 25, 0.96, 0.50),
    SubgroupResult("s2", 75, 0.53, 0.60),
)
_LOW_WEIGHT_REGRESSION = (
    SubgroupResult("major", 95, 0.83, 0.69),
    SubgroupResult("minor", 5, 0.40, 0.80),
)


def audit_confounding_control_suite() -> dict:
    controls: list[tuple[str, EvidenceRecord, bool]] = [
        ("valid-declared", _valid_record(_CONSISTENT), False),
        (
            "subgroup-regression",
            replace(
                _valid_record(_REGRESSING),
                reported_accuracy=0.6375,
                recomputed_accuracy=0.6375,
                baseline_reported_accuracy=0.575,
                baseline_recomputed_accuracy=0.575,
            ),
            True,
        ),
        (
            "aggregate-mismatch",
            replace(
                _valid_record(_CONSISTENT),
                reported_accuracy=0.90,
                recomputed_accuracy=0.90,
            ),
            True,
        ),
        ("no-subgroups", _valid_record(()), False),
        (
            "low-weight-regression",
            replace(
                _valid_record(_LOW_WEIGHT_REGRESSION),
                reported_accuracy=0.8085,
                recomputed_accuracy=0.8085,
                baseline_reported_accuracy=0.6955,
                baseline_recomputed_accuracy=0.6955,
            ),
            False,
        ),
    ]
    rows: list[dict] = []
    all_expected = True
    for name, record, expected_flag in controls:
        result = check_confounding(record)
        matched = result.flagged == expected_flag
        all_expected = all_expected and matched
        rows.append(
            {
                "control": name,
                "expected_flagged": expected_flag,
                "flagged": result.flagged,
                "evaluated": result.evaluated,
                "matched_expectation": matched,
                "failures": list(result.failures),
            }
        )
    return {
        "controls": len(rows),
        "all_expected": all_expected,
        "rows": rows,
    }


@dataclass(frozen=True, slots=True)
class ConfoundingCase:
    case_id: str
    defect: str
    record: EvidenceRecord
    expected_positive: bool
    expected_valid_experiment: bool


_CONSISTENT_POSITIVE = (
    SubgroupResult("s1", 50, 0.80, 0.68),
    SubgroupResult("s2", 50, 0.84, 0.72),
)
_CONSISTENT_NEGATIVE = (
    SubgroupResult("s1", 50, 0.66, 0.68),
    SubgroupResult("s2", 50, 0.70, 0.72),
)
_CONFOUNDED = (
    SubgroupResult("s1", 25, 0.94, 0.40),
    SubgroupResult("s2", 75, 0.78, 0.80),
)


def _shifted(
    subgroups: tuple[SubgroupResult, ...],
    delta: float,
) -> tuple[SubgroupResult, ...]:
    return tuple(
        SubgroupResult(
            group.subgroup_id,
            group.n,
            group.candidate_accuracy + delta,
            group.baseline_accuracy + delta,
        )
        for group in subgroups
    )


def _record_like(
    *,
    reported: float = 0.82,
    baseline_reported: float = 0.70,
    recomputed: float | None = None,
    baseline_recomputed: float | None = None,
    train=None,
    test=None,
    features=("f-1", "f-2"),
    seeds=(0, 1, 2),
    subgroups: tuple[SubgroupResult, ...] = (),
) -> EvidenceRecord:
    record = EvidenceRecord(
        experiment_id="confounding-case",
        train_ids=frozenset({"tr-1", "tr-2", "tr-3"}),
        test_ids=frozenset({"te-1", "te-2"}),
        feature_names=features,
        target_name="label",
        reported_accuracy=reported,
        recomputed_accuracy=reported if recomputed is None else recomputed,
        baseline_reported_accuracy=baseline_reported,
        baseline_recomputed_accuracy=(
            baseline_reported
            if baseline_recomputed is None
            else baseline_recomputed
        ),
        seeds=seeds,
        test_set_id="confounding-test-v1",
        subgroups=subgroups,
    )
    if train is not None:
        record = replace(record, train_ids=train)
    if test is not None:
        record = replace(record, test_ids=test)
    if features != ("f-1", "f-2"):
        record = replace(record, feature_names=features)
    return record


def generate_confounding_control_cases() -> list[ConfoundingCase]:
    cases: list[ConfoundingCase] = []
    for index in range(10):
        delta = index / 1000
        positive_groups = _shifted(_CONSISTENT_POSITIVE, delta)
        negative_groups = _shifted(_CONSISTENT_NEGATIVE, delta)
        confounded_groups = _shifted(_CONFOUNDED, delta)

        cases.append(
            ConfoundingCase(
                case_id=f"valid-positive-{index:02d}",
                defect="valid-positive",
                record=_record_like(
                    reported=0.82 + delta,
                    baseline_reported=0.70 + delta,
                    subgroups=positive_groups,
                ),
                expected_positive=True,
                expected_valid_experiment=True,
            )
        )
        cases.append(
            ConfoundingCase(
                case_id=f"valid-negative-{index:02d}",
                defect="valid-negative",
                record=_record_like(
                    reported=0.68 + delta,
                    baseline_reported=0.70 + delta,
                    subgroups=negative_groups,
                ),
                expected_positive=False,
                expected_valid_experiment=True,
            )
        )
        cases.append(
            ConfoundingCase(
                case_id=f"split-overlap-{index:02d}",
                defect="split-overlap",
                record=_record_like(
                    reported=0.82 + delta,
                    baseline_reported=0.70 + delta,
                    test=frozenset({"tr-1", f"te-{index}"}),
                    subgroups=positive_groups,
                ),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
        cases.append(
            ConfoundingCase(
                case_id=f"target-leakage-{index:02d}",
                defect="target-leakage",
                record=_record_like(
                    reported=0.82 + delta,
                    baseline_reported=0.70 + delta,
                    features=("f-1", "label"),
                    subgroups=positive_groups,
                ),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
        cases.append(
            ConfoundingCase(
                case_id=f"broken-baseline-{index:02d}",
                defect="broken-baseline",
                record=_record_like(
                    reported=0.82 + delta,
                    baseline_reported=0.70 + delta,
                    baseline_recomputed=0.64,
                    subgroups=positive_groups,
                ),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
        cases.append(
            ConfoundingCase(
                case_id=f"p-hacking-{index:02d}",
                defect="p-hacking",
                record=_record_like(
                    reported=0.82 + delta,
                    baseline_reported=0.70 + delta,
                    seeds=(0,),
                    subgroups=positive_groups,
                ),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
        cases.append(
            ConfoundingCase(
                case_id=f"unreproducible-{index:02d}",
                defect="unreproducible",
                record=_record_like(
                    reported=0.82 + delta,
                    baseline_reported=0.70 + delta,
                    recomputed=0.78,
                    subgroups=positive_groups,
                ),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
        cases.append(
            ConfoundingCase(
                case_id=f"confounded-declared-{index:02d}",
                defect="confounded-declared",
                record=_record_like(
                    reported=0.82 + delta,
                    baseline_reported=0.70 + delta,
                    subgroups=confounded_groups,
                ),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
        cases.append(
            ConfoundingCase(
                case_id=f"confounded-undeclared-{index:02d}",
                defect="confounded-undeclared",
                record=_record_like(
                    reported=0.82 + delta,
                    baseline_reported=0.70 + delta,
                ),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
    return cases


def _claim_summary(cases: list[ConfoundingCase], claims: dict[str, bool]) -> dict:
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


def run_confounding_control_probe(
    cases: list[ConfoundingCase] | None = None,
) -> dict:
    if cases is None:
        cases = generate_confounding_control_cases()
    gate = EvidenceGate()
    naive_claims: dict[str, bool] = {}
    gated_v0_claims: dict[str, bool] = {}
    gated_v1_claims: dict[str, bool] = {}
    checks: dict[str, ConfoundingCheck] = {}

    for case in cases:
        record = case.record
        naive_claims[case.case_id] = (
            record.reported_accuracy > record.baseline_reported_accuracy
        )
        gate_passed = gate.evaluate(record).passed
        gated_v0_claims[case.case_id] = (
            gate_passed
            and record.reported_accuracy > record.baseline_reported_accuracy
        )
        confounding = check_confounding(record)
        checks[case.case_id] = confounding
        gated_v1_claims[case.case_id] = (
            gated_v0_claims[case.case_id] and not confounding.flagged
        )

    declared = [case for case in cases if case.defect == "confounded-declared"]
    undeclared = [
        case for case in cases if case.defect == "confounded-undeclared"
    ]
    valid_cases = [
        case
        for case in cases
        if case.defect in {"valid-positive", "valid-negative"}
    ]

    return {
        "status": "harness-validation",
        "scientific_result": False,
        "suite": "confounding control v1",
        "cases": len(cases),
        "policies": {
            "naive": _claim_summary(cases, naive_claims),
            "gated_v0": _claim_summary(cases, gated_v0_claims),
            "gated_v1": _claim_summary(cases, gated_v1_claims),
        },
        "confounding_control": {
            "confounded_declared_cases": len(declared),
            "confounded_declared_detected": sum(
                checks[case.case_id].flagged for case in declared
            ),
            "confounded_undeclared_cases": len(undeclared),
            "confounded_undeclared_detected": sum(
                checks[case.case_id].flagged for case in undeclared
            ),
            "residual_blind_spot_cases": sum(
                not checks[case.case_id].flagged for case in undeclared
            ),
            "false_alarms_on_valid_cases": sum(
                checks[case.case_id].flagged for case in valid_cases
            ),
            "declared_evaluable_rate": (
                sum(checks[case.case_id].evaluated for case in declared)
                / len(declared)
                if declared
                else 0.0
            ),
            "undeclared_evaluable_rate": (
                sum(checks[case.case_id].evaluated for case in undeclared)
                / len(undeclared)
                if undeclared
                else 0.0
            ),
        },
        "notes": [
            "The 90 cases are synthetic controls, not a live research-agent benchmark.",
            "gated_v0 is the v0 Evidence Gate; gated_v1 adds the stratified confounding control.",
            "Confounding that is not declared as a subgroup breakdown stays undetectable, so the residual blind spot is reported rather than removed.",
        ],
    }
