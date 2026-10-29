from longrun.probes.goal_drift_monitor import run_goal_drift_monitor_probe


def test_goal_drift_monitor_reports_heldout_metrics():
    result = run_goal_drift_monitor_probe(seed=29, episodes=60, steps=40)
    assert result["status"] == "harness-validation"
    assert result["scientific_result"] is False
    assert result["traces"] == 180
    assert result["train_traces"] + result["test_traces"] == 180
    assert 0.0 <= result["metrics"]["auroc"] <= 1.0
    assert result["metrics"]["auroc"] > 0.6
    assert result["metrics"]["false_alarm_rate"] <= 1.0
    assert 0.0 <= result["metrics"]["intervention_recovery_rate"] <= 1.0


def test_goal_drift_monitor_is_deterministic():
    first = run_goal_drift_monitor_probe(seed=29, episodes=20, steps=30)
    second = run_goal_drift_monitor_probe(seed=29, episodes=20, steps=30)
    assert first == second


def test_goal_drift_monitor_keeps_model_claim_boundary():
    result = run_goal_drift_monitor_probe(seed=29, episodes=20, steps=20)
    assert "synthetic" in result["scope"]
    assert result["model"]["kind"] == "logistic-regression"
