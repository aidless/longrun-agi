from longrun.probes.adaptive_controller import run_adaptive_controller_probe


def test_adaptive_controller_reports_cost_and_stability():
    result = run_adaptive_controller_probe(seed=41, train_episodes=600)
    assert result["status"] == "harness-validation"
    assert result["scientific_result"] is False
    assert "adaptive" in result["policies"]
    for policy in result["policies"].values():
        assert 0.0 <= policy["success_rate"] <= 1.0
        assert policy["mean_cost"] >= 0.0
        assert policy["cost_per_success"] >= 0.0
        assert 0.0 <= policy["calibration_error"] <= 1.0
        assert policy["stability_range"] >= 0.0


def test_adaptive_controller_is_deterministic():
    first = run_adaptive_controller_probe(seed=41, train_episodes=120)
    second = run_adaptive_controller_probe(seed=41, train_episodes=120)
    assert first == second


def test_adaptive_controller_has_all_runtime_actions():
    result = run_adaptive_controller_probe(seed=41, train_episodes=120)
    counts = result["policies"]["adaptive"]["action_counts"]
    assert set(counts) == {
        "retrieve",
        "reflect",
        "tool",
        "write-memory",
        "stop",
    }
