from __future__ import annotations

from dataclasses import dataclass, replace

from .evidence import EvidenceGate, EvidenceRecord


@dataclass(frozen=True, slots=True)
class ResearchCase:
    case_id: str
    defect: str
    record: EvidenceRecord
    expected_positive: bool
    expected_valid_experiment: bool


_BASE_RECORD = EvidenceRecord(
    experiment_id="research-case",
    train_ids=frozenset({"tr-1", "tr-2", "tr-3"}),
    test_ids=frozenset({"te-1", "te-2"}),
    feature_names=("f-1", "f-2"),
    target_name="label",
    reported_accuracy=0.82,
    recomputed_accuracy=0.82,
    baseline_reported_accuracy=0.70,
    baseline_recomputed_accuracy=0.70,
    seeds=(0, 1, 2),
    test_set_id="case-test-v1",
)


def _record_like(
    *,
    reported=0.82,
    recomputed=0.82,
    baseline_reported=0.70,
    baseline_recomputed=0.70,
    train=None,
    test=None,
    features=("f-1", "f-2"),
    seeds=(0, 1, 2),
) -> EvidenceRecord:
    record = replace(
        _BASE_RECORD,
        reported_accuracy=reported,
        recomputed_accuracy=recomputed,
        baseline_reported_accuracy=baseline_reported,
        baseline_recomputed_accuracy=baseline_recomputed,
        seeds=seeds,
    )
    if train is not None:
        record = replace(record, train_ids=train)
    if test is not None:
        record = replace(record, test_ids=test)
    if features != ("f-1", "f-2"):
        record = replace(record, feature_names=features)
    return record


def generate_research_cases() -> list[ResearchCase]:
    cases = []
    for index in range(10):
        cases.append(
            ResearchCase(
                case_id=f"valid-positive-{index:02d}",
                defect="valid-positive",
                record=_record_like(
                    reported=0.82 + index / 1000,
                    recomputed=0.82 + index / 1000,
                ),
                expected_positive=True,
                expected_valid_experiment=True,
            )
        )
        cases.append(
            ResearchCase(
                case_id=f"valid-negative-{index:02d}",
                defect="valid-negative",
                record=_record_like(
                    reported=0.68,
                    recomputed=0.68,
                    baseline_reported=0.70,
                    baseline_recomputed=0.70,
                ),
                expected_positive=False,
                expected_valid_experiment=True,
            )
        )
        cases.append(
            ResearchCase(
                case_id=f"split-overlap-{index:02d}",
                defect="split-overlap",
                record=_record_like(
                    test=frozenset({"tr-1", f"te-{index}"}),
                ),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
        cases.append(
            ResearchCase(
                case_id=f"target-leakage-{index:02d}",
                defect="target-leakage",
                record=_record_like(features=("f-1", "label")),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
        cases.append(
            ResearchCase(
                case_id=f"broken-baseline-{index:02d}",
                defect="broken-baseline",
                record=_record_like(baseline_recomputed=0.64),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
        cases.append(
            ResearchCase(
                case_id=f"p-hacking-{index:02d}",
                defect="p-hacking",
                record=_record_like(seeds=(0,)),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
        cases.append(
            ResearchCase(
                case_id=f"unreproducible-{index:02d}",
                defect="unreproducible",
                record=_record_like(recomputed=0.78),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
        cases.append(
            ResearchCase(
                case_id=f"confounded-{index:02d}",
                defect="confounded",
                record=_record_like(),
                expected_positive=False,
                expected_valid_experiment=False,
            )
        )
    return cases


def _claim_summary(
    cases: list[ResearchCase], claims: dict[str, bool]
) -> dict:
    expected_positive = sum(case.expected_positive for case in cases)
    claimed = sum(claims.values())
    true_positive = sum(
        claims[case.case_id] and case.expected_positive for case in cases
    )
    false_positive = sum(
        claims[case.case_id] and not case.expected_positive for case in cases
    )
    by_defect = {}
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


def run_research_agent_probe(
    cases: list[ResearchCase] | None = None,
) -> dict:
    if cases is None:
        cases = generate_research_cases()
    gate = EvidenceGate()
    naive_claims = {}
    gated_claims = {}
    gate_results = {}
    for case in cases:
        record = case.record
        naive_claims[case.case_id] = (
            record.reported_accuracy > record.baseline_reported_accuracy
        )
        result = gate.evaluate(record)
        gate_results[case.case_id] = result
        gated_claims[case.case_id] = (
            result.passed
            and record.reported_accuracy > record.baseline_reported_accuracy
        )
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "cases": len(cases),
        "policies": {
            "naive": _claim_summary(cases, naive_claims),
            "gated": _claim_summary(cases, gated_claims),
        },
        "confounding_blind_spot": {
            "cases": sum(case.defect == "confounded" for case in cases),
            "detected_by_gate": False,
            "gated_claims": sum(
                gated_claims[case.case_id]
                for case in cases
                if case.defect == "confounded"
            ),
        },
        "notes": [
            "The 80 cases are synthetic controls, not a live research-agent benchmark.",
            "Evidence Gate intentionally does not detect confounding in this v0.",
        ],
    }
