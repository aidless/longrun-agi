from longrun.probes.compute import run_compute_probe


def test_compute_controller_never_exceeds_budget():
    result = run_compute_probe(seed=19, jobs=40, budget=60)
    for policy in result["policies"].values():
        assert policy["spent"] <= result["config"]["budget"]
        assert policy["overspend"] is False


def test_compute_probe_compares_scheduling_policies():
    result = run_compute_probe(seed=19, jobs=40, budget=60)
    assert set(result["policies"]) == {
        "fifo",
        "shortest-job",
        "value-density",
        "safe-value-density",
        "random",
    }
    assert result["policies"]["value-density"]["value"] >= 0.0
    assert result["policies"]["safe-value-density"]["deadline_misses"] <= (
        result["policies"]["fifo"]["deadline_misses"]
        + result["config"]["jobs"]
    )


def test_compute_probe_is_deterministic():
    assert run_compute_probe(seed=19, jobs=20, budget=40) == (
        run_compute_probe(seed=19, jobs=20, budget=40)
    )


def test_compute_probe_checks_seed_robustness():
    result = run_compute_probe(seed=19, jobs=40, budget=60)
    robustness = result["robustness"]
    assert robustness["seeds"] == result["config"]["robustness_seeds"]
    assert 0.0 <= robustness["value_density_wins_share"] <= 1.0
    assert robustness["best_policy_frequency"]
    assert all(
        count <= robustness["seeds"]
        for count in robustness["best_policy_frequency"].values()
    )


def test_safe_value_density_has_no_executed_deadline_miss():
    result = run_compute_probe(seed=19, jobs=80, budget=120)
    assert result["policies"]["safe-value-density"]["deadline_misses"] == 0
