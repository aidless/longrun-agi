from longrun.runtime.real_faults import FAULTS, run_real_fault_matrix


def test_real_fault_matrix_has_expected_controller_contrast():
    result = run_real_fault_matrix()
    assert result["status"] == "harness-validation"
    assert result["scientific_result"] is False
    assert result["config"]["faults"] == 5
    assert result["config"]["network_calls"] == 0
    policies = result["by_policy"]
    assert policies["retry-only"]["success_rate"] < 1.0
    assert policies["rollback"]["success_rate"] < 1.0
    assert policies["state-check-replan"]["success_rate"] == 1.0
    assert policies["replan"]["success_rate"] == 1.0
    assert policies["state-check-replan"]["replans"] > 0
    assert policies["replan"]["replans"] > 0


def test_every_fault_and_policy_is_recorded_once():
    result = run_real_fault_matrix()
    pairs = {(row["fault"], row["policy"]) for row in result["rows"]}
    assert len(result["rows"]) == 20
    assert len(pairs) == 20
    assert {row["fault"] for row in result["rows"]} == set(FAULTS)


def test_real_fault_matrix_is_deterministic():
    first = run_real_fault_matrix()
    second = run_real_fault_matrix()
    for first_policy, second_policy in zip(
        first["by_policy"].values(), second["by_policy"].values(), strict=True
    ):
        for key in ("cases", "successes", "success_rate"):
            assert first_policy[key] == second_policy[key]
