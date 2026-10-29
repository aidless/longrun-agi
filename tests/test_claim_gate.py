import json

from longrun.cli import main
from longrun.controls.claim_gate import (
    EvidenceClaimGate,
    generate_claim_schema_cases,
    run_claim_schema_probe,
)
from longrun.controls.evidence import EvidenceRecord, SubgroupResult


def _record(
    *,
    reported: float = 0.82,
    baseline: float = 0.70,
    subgroups: tuple[SubgroupResult, ...] = (),
    test_n: int | None = None,
    test_ids: frozenset[str] = frozenset({"te-1", "te-2"}),
) -> EvidenceRecord:
    return EvidenceRecord(
        experiment_id="claim-schema-case",
        train_ids=frozenset({"tr-1", "tr-2", "tr-3"}),
        test_ids=test_ids,
        feature_names=("f-1", "f-2"),
        target_name="label",
        reported_accuracy=reported,
        recomputed_accuracy=reported,
        baseline_reported_accuracy=baseline,
        baseline_recomputed_accuracy=baseline,
        seeds=(0, 1, 2),
        test_set_id="claim-schema-test-v1",
        subgroups=subgroups,
        test_n=test_n,
    )


_CONSISTENT = (
    SubgroupResult("s1", 50, 0.80, 0.68),
    SubgroupResult("s2", 50, 0.84, 0.72),
)
_CONFOUNDED = (
    SubgroupResult("s1", 25, 0.94, 0.40),
    SubgroupResult("s2", 75, 0.78, 0.80),
)


def test_declared_consistent_subgroups_are_accepted():
    result = EvidenceClaimGate().evaluate(
        _record(subgroups=_CONSISTENT, test_n=100)
    )
    assert result.status == "accepted"
    assert result.claim_accepted is True
    assert result.evidence_valid is True
    assert result.schema_valid is True
    assert result.confounding_evaluated is True
    assert result.confounding_flagged is False
    assert result.failures == ()


def test_declared_confounding_is_rejected():
    result = EvidenceClaimGate().evaluate(
        _record(subgroups=_CONFOUNDED, test_n=100)
    )
    assert result.status == "rejected"
    assert result.claim_accepted is False
    assert result.confounding_evaluated is True
    assert result.confounding_flagged is True
    assert any("subgroup regression" in failure for failure in result.failures)


def test_missing_declaration_blocks_positive_claim_as_non_evaluable():
    result = EvidenceClaimGate().evaluate(_record())
    assert result.status == "non-evaluable"
    assert result.claim_accepted is False
    assert result.evidence_valid is True
    assert result.schema_valid is False
    assert result.confounding_evaluated is False
    assert result.metrics["missing_required_declaration"] is True
    assert any(
        "requires a declared subgroup" in failure for failure in result.failures
    )


def test_negative_result_without_subgroups_is_accepted():
    result = EvidenceClaimGate().evaluate(
        _record(reported=0.68, baseline=0.70)
    )
    assert result.status == "accepted"
    assert result.claim_accepted is True
    assert result.schema_valid is True
    assert result.confounding_evaluated is False


def test_zero_improvement_without_subgroups_is_accepted_as_negative():
    result = EvidenceClaimGate().evaluate(_record(reported=0.70, baseline=0.70))
    assert result.status == "accepted"
    assert result.metrics["positive_improvement"] is False


def test_duplicate_subgroup_ids_are_rejected():
    duplicates = (
        SubgroupResult("duplicate", 50, 0.80, 0.68),
        SubgroupResult("duplicate", 50, 0.84, 0.72),
    )
    result = EvidenceClaimGate().evaluate(
        _record(subgroups=duplicates, test_n=100)
    )
    assert result.status == "rejected"
    assert result.schema_valid is False
    assert any("duplicate subgroup ids" in failure for failure in result.failures)


def test_empty_subgroup_id_is_rejected():
    subgroups = (
        SubgroupResult(" ", 50, 0.80, 0.68),
        SubgroupResult("s2", 50, 0.84, 0.72),
    )
    result = EvidenceClaimGate().evaluate(
        _record(subgroups=subgroups, test_n=100)
    )
    assert result.status == "rejected"
    assert any("ids must be non-empty" in failure for failure in result.failures)


def test_nonpositive_subgroup_sample_size_is_rejected():
    subgroups = (
        SubgroupResult("s1", 0, 0.80, 0.68),
        SubgroupResult("s2", 100, 0.82, 0.70),
    )
    result = EvidenceClaimGate().evaluate(
        _record(subgroups=subgroups, test_n=100)
    )
    assert result.status == "rejected"
    assert any("sample sizes must be positive" in failure for failure in result.failures)


def test_out_of_range_subgroup_accuracy_is_rejected():
    subgroups = (
        SubgroupResult("s1", 50, 1.20, 0.68),
        SubgroupResult("s2", 50, 0.44, 0.72),
    )
    result = EvidenceClaimGate().evaluate(
        _record(subgroups=subgroups, test_n=100)
    )
    assert result.status == "rejected"
    assert any("accuracies must be within" in failure for failure in result.failures)


def test_missing_test_n_is_rejected_for_declared_subgroups():
    result = EvidenceClaimGate().evaluate(_record(subgroups=_CONSISTENT))
    assert result.status == "rejected"
    assert result.schema_valid is False
    assert any("test_n is required" in failure for failure in result.failures)


def test_mismatched_test_n_is_rejected():
    result = EvidenceClaimGate().evaluate(
        _record(subgroups=_CONSISTENT, test_n=99)
    )
    assert result.status == "rejected"
    assert any("do not sum to test_n" in failure for failure in result.failures)


def test_base_evidence_failure_remains_rejected():
    result = EvidenceClaimGate().evaluate(
        _record(
            subgroups=_CONSISTENT,
            test_n=100,
            test_ids=frozenset({"tr-1", "te-2"}),
        )
    )
    assert result.status == "rejected"
    assert result.evidence_valid is False
    assert any("split overlap" in failure for failure in result.failures)


def test_optional_policy_accepts_missing_declaration_for_compatibility():
    result = EvidenceClaimGate(
        require_subgroups_for_positive_claims=False
    ).evaluate(_record())
    assert result.status == "accepted"
    assert result.schema_valid is True
    assert result.confounding_evaluated is False


def test_claim_schema_probe_has_expected_strict_tradeoff():
    result = run_claim_schema_probe()
    assert result["cases"] == 110
    assert result["source_control_cases"] == 90
    assert result["added_cases"] == 20
    assert result["status"] == "harness-validation"
    assert result["scientific_result"] is False
    policies = result["policies"]
    assert policies["naive"]["claims"] == 100
    assert policies["naive"]["false_discoveries"] == 80
    assert policies["gated_v0"]["claims"] == 50
    assert policies["gated_v0"]["false_discoveries"] == 30
    assert policies["gated_v1"]["claims"] == 40
    assert policies["gated_v1"]["false_discoveries"] == 20
    assert policies["strict_v2"]["claims"] == 10
    assert policies["strict_v2"]["false_discoveries"] == 0
    assert policies["strict_v2"]["valid_discovery_rate"] == 0.5
    assert result["decision_counts"] == {
        "accepted": 20,
        "rejected": 70,
        "non-evaluable": 20,
    }
    assert result["schema_control"]["invalid_schema_rejected"] == 10
    assert result["confounding_control"]["confounded_declared_detected"] == 10
    assert result["confounding_control"]["confounded_undeclared_detected"] == 0
    assert (
        result["confounding_control"][
            "confounded_undeclared_blocked_non_evaluable"
        ]
        == 10
    )
    assert result["confounding_control"]["residual_accepted_claims"] == 0
    assert result["valid_undeclared_cost"] == {
        "cases": 10,
        "accepted_claims": 0,
        "non_evaluable_claims": 10,
    }


def test_claim_schema_case_set_is_deterministic_and_well_formed():
    cases = generate_claim_schema_cases()
    assert len(cases) == 110
    assert len({case.case_id for case in cases}) == 110
    assert {case.defect for case in cases} == {
        "valid-positive",
        "valid-negative",
        "split-overlap",
        "target-leakage",
        "broken-baseline",
        "p-hacking",
        "unreproducible",
        "confounded-declared",
        "confounded-undeclared",
        "valid-positive-undeclared",
        "invalid-subgroup-declaration",
    }
    assert run_claim_schema_probe() == run_claim_schema_probe()


def test_claim_schema_cli_writes_output(tmp_path):
    output = tmp_path / "claim-schema.json"
    assert main(["claim-schema", "--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["cases"] == 110
    assert payload["policies"]["strict_v2"]["false_discoveries"] == 0
    assert payload["valid_undeclared_cost"]["non_evaluable_claims"] == 10
