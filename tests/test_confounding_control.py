import json

from longrun.cli import main
from longrun.controls.confounding import (
    audit_confounding_control_suite,
    check_confounding,
    generate_confounding_control_cases,
    run_confounding_control_probe,
)
from longrun.controls.evidence import EvidenceRecord, SubgroupResult


def _record(
    reported: float = 0.82,
    baseline: float = 0.70,
    subgroups: tuple[SubgroupResult, ...] = (),
) -> EvidenceRecord:
    return EvidenceRecord(
        experiment_id="confounding-case",
        train_ids=frozenset({"tr-1", "tr-2", "tr-3"}),
        test_ids=frozenset({"te-1", "te-2"}),
        feature_names=("f-1", "f-2"),
        target_name="label",
        reported_accuracy=reported,
        recomputed_accuracy=reported,
        baseline_reported_accuracy=baseline,
        baseline_recomputed_accuracy=baseline,
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


def test_consistent_declared_subgroups_are_not_flagged():
    result = check_confounding(_record(subgroups=_CONSISTENT))
    assert result.evaluated is True
    assert result.flagged is False
    assert result.failures == ()
    assert result.metrics["min_subgroup_improvement"] > 0.0


def test_subgroup_regression_is_flagged():
    result = check_confounding(
        _record(reported=0.6375, baseline=0.575, subgroups=_REGRESSING)
    )
    assert result.evaluated is True
    assert result.flagged is True
    assert any("subgroup regression" in failure for failure in result.failures)
    assert result.metrics["crude_improvement"] > 0.0
    assert result.metrics["min_subgroup_improvement"] < 0.0


def test_low_weight_regression_is_not_flagged():
    subgroups = (
        SubgroupResult("major", 95, 0.83, 0.69),
        SubgroupResult("minor", 5, 0.40, 0.80),
    )
    result = check_confounding(
        _record(reported=0.8085, baseline=0.6955, subgroups=subgroups)
    )
    assert result.flagged is False
    assert result.metrics["min_subgroup_weight"] < 0.2


def test_missing_subgroups_are_reported_as_not_evaluable():
    result = check_confounding(_record())
    assert result.evaluated is False
    assert result.flagged is False
    assert result.failures == ()


def test_subgroup_aggregate_must_reproduce_reported_accuracy():
    result = check_confounding(
        _record(reported=0.90, baseline=0.70, subgroups=_CONSISTENT)
    )
    assert result.flagged is True
    assert any("does not reproduce" in failure for failure in result.failures)


def test_confounding_control_suite_matches_expected_outcomes():
    result = audit_confounding_control_suite()
    assert result["all_expected"] is True
    assert result["controls"] == 5
    assert result["rows"][0]["control"] == "valid-declared"


def test_probe_detects_declared_confounding_and_keeps_valid_cases():
    result = run_confounding_control_probe()
    assert result["cases"] == 90
    assert result["status"] == "harness-validation"
    assert result["scientific_result"] is False
    control = result["confounding_control"]
    assert control["confounded_declared_cases"] == 10
    assert control["confounded_declared_detected"] == 10
    assert control["confounded_undeclared_cases"] == 10
    assert control["confounded_undeclared_detected"] == 0
    assert control["residual_blind_spot_cases"] == 10
    assert control["false_alarms_on_valid_cases"] == 0
    policies = result["policies"]
    assert policies["gated_v0"]["false_discoveries"] == 20
    assert policies["gated_v1"]["false_discoveries"] == 10
    assert policies["naive"]["false_discoveries"] == 70
    assert policies["gated_v1"]["valid_discovery_rate"] == 1.0
    assert policies["gated_v0"]["valid_discovery_rate"] == 1.0


def test_probe_case_set_is_deterministic_and_well_formed():
    cases = generate_confounding_control_cases()
    assert len(cases) == 90
    assert len({case.case_id for case in cases}) == 90
    assert result_categories(cases) == {
        "valid-positive",
        "valid-negative",
        "split-overlap",
        "target-leakage",
        "broken-baseline",
        "p-hacking",
        "unreproducible",
        "confounded-declared",
        "confounded-undeclared",
    }
    assert run_confounding_control_probe() == run_confounding_control_probe()


def test_cli_writes_confounding_control_output(tmp_path):
    output = tmp_path / "confounding-control.json"
    assert main(["confounding-control", "--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["cases"] == 90
    assert payload["policies"]["gated_v1"]["false_discoveries"] == 10
    assert payload["confounding_control"]["residual_blind_spot_cases"] == 10


def result_categories(cases) -> set[str]:
    return {case.defect for case in cases}
