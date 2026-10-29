from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class SubgroupResult:
    """A declared subgroup with its own candidate and baseline accuracy."""

    subgroup_id: str
    n: int
    candidate_accuracy: float
    baseline_accuracy: float

    @property
    def improvement(self) -> float:
        return self.candidate_accuracy - self.baseline_accuracy


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    experiment_id: str
    train_ids: frozenset[str]
    test_ids: frozenset[str]
    feature_names: tuple[str, ...]
    target_name: str
    reported_accuracy: float
    recomputed_accuracy: float
    baseline_reported_accuracy: float
    baseline_recomputed_accuracy: float
    seeds: tuple[int, ...]
    test_set_id: str
    subgroups: tuple[SubgroupResult, ...] = ()
    test_n: int | None = None


@dataclass(frozen=True, slots=True)
class GateResult:
    passed: bool
    failures: tuple[str, ...]
    warnings: tuple[str, ...]


class EvidenceGate:
    def __init__(self, tolerance: float = 1e-6, min_seeds: int = 2):
        if tolerance < 0:
            raise ValueError("tolerance must be non-negative")
        if min_seeds < 1:
            raise ValueError("min_seeds must be positive")
        self.tolerance = tolerance
        self.min_seeds = min_seeds

    def evaluate(self, record: EvidenceRecord) -> GateResult:
        failures: list[str] = []
        warnings: list[str] = []
        overlap = record.train_ids & record.test_ids
        if overlap:
            failures.append(f"train/test split overlap: {len(overlap)} ids")
        if record.target_name in record.feature_names:
            failures.append("target leakage: target is also listed as a feature")
        if not 0.0 <= record.reported_accuracy <= 1.0:
            failures.append("reported accuracy is outside [0, 1]")
        if not 0.0 <= record.recomputed_accuracy <= 1.0:
            failures.append("recomputed accuracy is outside [0, 1]")
        if abs(record.reported_accuracy - record.recomputed_accuracy) > self.tolerance:
            failures.append("reported accuracy does not match recomputation")
        if abs(
            record.baseline_reported_accuracy - record.baseline_recomputed_accuracy
        ) > self.tolerance:
            failures.append("baseline accuracy does not match recomputation")
        if len(set(record.seeds)) < self.min_seeds:
            failures.append("fewer than two distinct seeds")
        if record.test_set_id.strip() == "":
            failures.append("test set id is empty")
        if record.reported_accuracy < record.baseline_reported_accuracy:
            warnings.append("reported accuracy is below the reported baseline")
        return GateResult(
            passed=not failures,
            failures=tuple(failures),
            warnings=tuple(warnings),
        )

    def run_ablation(self) -> dict:
        valid = _valid_record()
        variants = {
            "split_overlap": replace(
                valid,
                test_ids=frozenset({"tr-1", "te-2"}),
            ),
            "target_leakage": replace(valid, feature_names=("f-1", "label")),
            "reported_mismatch": replace(valid, recomputed_accuracy=0.79),
            "baseline_mismatch": replace(
                valid,
                baseline_recomputed_accuracy=0.68,
            ),
            "one_seed": replace(valid, seeds=(0,)),
            "metric_overflow": replace(valid, reported_accuracy=1.20),
        }
        rows = []
        for name, record in variants.items():
            clean = self.evaluate(valid)
            degraded = self.evaluate(record)
            rows.append(
                {
                    "check": name,
                    "clean_passed": clean.passed,
                    "degraded_passed": degraded.passed,
                    "expected_degraded_failure": True,
                }
            )
        return {
            "status": "harness-validation",
            "scientific_result": False,
            "checks": rows,
            "all_ablation_effects_correct": all(
                row["clean_passed"]
                and not row["degraded_passed"]
                and row["expected_degraded_failure"]
                for row in rows
            ),
        }


def _valid_record() -> EvidenceRecord:
    return EvidenceRecord(
        experiment_id="valid-control",
        train_ids=frozenset({"tr-1", "tr-2", "tr-3"}),
        test_ids=frozenset({"te-1", "te-2"}),
        feature_names=("f-1", "f-2", "f-3"),
        target_name="label",
        reported_accuracy=0.81,
        recomputed_accuracy=0.81,
        baseline_reported_accuracy=0.70,
        baseline_recomputed_accuracy=0.70,
        seeds=(0, 1, 2),
        test_set_id="dev-test-v1",
    )


def audit_control_suite() -> dict:
    gate = EvidenceGate()
    valid = _valid_record()
    controls: dict[str, tuple[EvidenceRecord, bool]] = {
        "valid": (valid, True),
        "split_overlap": (replace(valid, test_ids=frozenset({"tr-1", "te-2"})), False),
        "target_leakage": (replace(valid, feature_names=("f-1", "label")), False),
        "reported_mismatch": (replace(valid, recomputed_accuracy=0.79), False),
        "baseline_mismatch": (replace(valid, baseline_recomputed_accuracy=0.68), False),
        "one_seed": (replace(valid, seeds=(0,)), False),
        "metric_overflow": (replace(valid, reported_accuracy=1.20), False),
    }
    rows: list[dict] = []
    all_expected = True
    for name, (record, expected_pass) in controls.items():
        result = gate.evaluate(record)
        matched = result.passed == expected_pass
        all_expected = all_expected and matched
        rows.append(
            {
                "control": name,
                "expected_pass": expected_pass,
                "gate_passed": result.passed,
                "matched_expectation": matched,
                "failures": list(result.failures),
                "warnings": list(result.warnings),
            }
        )
    return {
        "controls": len(rows),
        "all_expected": all_expected,
        "rows": rows,
    }
