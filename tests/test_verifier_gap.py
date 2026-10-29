from longrun.probes.verifier_gap import run_verifier_gap_probe


def test_verifier_gap_separates_proxy_and_true_objectives():
    result = run_verifier_gap_probe()

    proxy = result["policies"]["proxy"]
    true = result["policies"]["true"]
    assert proxy["proxy_success"] is True
    assert true["true_success"] is True
    assert proxy["hazard_hits"] == 1
    assert true["hazard_hits"] == 0
    assert result["verifier_gap"] > 0.0


def test_verifier_gap_is_deterministic_for_fixed_seed():
    first = run_verifier_gap_probe(seed=42)
    second = run_verifier_gap_probe(seed=42)
    assert first == second


def test_q_learning_probe_reports_reward_sensitive_policies():
    result = run_verifier_gap_probe(seed=42, q_learning_episodes=150)
    q_proxy = result["q_learning"]["proxy"]
    q_true = result["q_learning"]["true"]
    assert q_proxy["episodes"] == 150
    assert q_true["episodes"] == 150
    assert q_proxy["actions"]
    assert q_true["actions"]
    assert q_proxy["greedy_action"] == "skip-verification-and-stop"
    assert q_true["greedy_action"] == "verify"
    assert q_proxy["mean_final_true_reward"] < q_true["mean_final_true_reward"]
    assert q_proxy["final_hazard_rate"] > q_true["final_hazard_rate"]
