from longrun.controls.evidence import EvidenceGate


def test_each_evidence_gate_check_has_an_ablation():
    result = EvidenceGate().run_ablation()
    assert result["status"] == "harness-validation"
    assert result["all_ablation_effects_correct"] is True
    assert result["checks"]
    for row in result["checks"]:
        assert row["clean_passed"] is True
        assert row["degraded_passed"] is False
