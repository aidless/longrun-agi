from longrun.probes.world_model_calibration import (
    run_world_model_calibration_probe,
)


def test_calibration_probe_reports_uncertainty_and_planning_metrics():
    result = run_world_model_calibration_probe(seed=17)
    assert result["status"] == "harness-validation"
    assert result["scientific_result"] is False
    assert result["data"]["train_pairs"] > 0
    assert result["data"]["ood_pairs"] > 0
    assert 0.0 <= result["metrics"]["id_accuracy"] <= 1.0
    assert 0.0 <= result["metrics"]["ood_accuracy"] <= 1.0
    assert result["metrics"]["ood_mean_uncertainty"] > (
        result["metrics"]["id_mean_uncertainty"]
    )
    assert 0.0 <= result["metrics"]["ood_error_auroc"] <= 1.0
    assert "uncertainty_penalized" in result["planning"]
    assert "argmax" in result["planning"]


def test_calibration_probe_is_deterministic():
    first = run_world_model_calibration_probe(seed=17, samples_per_pair=12)
    second = run_world_model_calibration_probe(seed=17, samples_per_pair=12)
    assert first == second


def test_calibration_probe_reports_sample_efficiency_and_planning():
    result = run_world_model_calibration_probe(seed=23, samples_per_pair=20)
    assert set(result["sample_efficiency"]) == {1, 2, 5, 20}
    assert all(
        0.0 <= row["id_accuracy"] <= 1.0
        for row in result["sample_efficiency"].values()
    )
    assert result["planning"]["argmax"]["successes"] >= 0
    assert result["planning"]["uncertainty_penalized"]["successes"] >= 0
