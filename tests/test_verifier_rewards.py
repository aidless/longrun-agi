from longrun.probes.verifier_rewards import run_verifier_reward_probe


def test_verifier_reward_probe_reports_all_reward_modes():
    result = run_verifier_reward_probe(seed=31, train_episodes=220)
    assert result["status"] == "harness-validation"
    assert result["scientific_result"] is False
    assert set(result["policies"]) == {
        "answer",
        "process",
        "self-verification",
        "ensemble-disagreement",
    }
    for policy in result["policies"].values():
        assert 0.0 <= policy["id_success_rate"] <= 1.0
        assert 0.0 <= policy["ood_success_rate"] <= 1.0
        assert 0.0 <= policy["reward_hacking_rate"] <= 1.0
        assert 0.0 <= policy["id_calibration_error"] <= 1.0
        assert policy["mean_reasoning_cost"] >= 0


def test_verifier_reward_probe_is_deterministic():
    first = run_verifier_reward_probe(seed=31, train_episodes=100)
    second = run_verifier_reward_probe(seed=31, train_episodes=100)
    assert first == second


def test_ensemble_reward_improves_ood_transfer_at_extra_cost():
    result = run_verifier_reward_probe(seed=31, train_episodes=600)
    answer = result["policies"]["answer"]
    ensemble = result["policies"]["ensemble-disagreement"]
    self_verify = result["policies"]["self-verification"]
    assert ensemble["ood_success_rate"] > answer["ood_success_rate"]
    assert ensemble["ood_transfer_drop"] < answer["ood_transfer_drop"]
    assert ensemble["mean_reasoning_cost"] > answer["mean_reasoning_cost"]
    assert 0.0 <= self_verify["reward_hacking_rate"] <= 1.0
