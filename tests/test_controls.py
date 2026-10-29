from longrun.controls.evidence import EvidenceGate, audit_control_suite


def test_control_suite_matches_expected_outcomes():
    result = audit_control_suite()
    assert result["all_expected"] is True
    assert result["controls"] == 7
    rejected = [row for row in result["rows"] if not row["gate_passed"]]
    assert len(rejected) == 6


def test_gate_is_not_a_general_integrity_claim():
    # The gate only checks the explicitly implemented deterministic controls.
    gate = EvidenceGate()
    valid = audit_control_suite()["rows"][0]
    assert valid["control"] == "valid"
    assert gate.tolerance == 1e-6
