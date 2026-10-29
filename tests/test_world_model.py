from longrun.probes.world_model import run_world_model_probe


def test_history_world_model_beats_one_step_model():
    result = run_world_model_probe(seed=7)
    models = result["models"]
    assert models["lag-1"]["one_step_accuracy"] < 1.0
    assert (
        models["lag-2"]["one_step_accuracy"]
        > models["lag-1"]["one_step_accuracy"]
    )
    assert models["lag-2"]["unique_contexts"] > models["lag-1"]["unique_contexts"]


def test_world_model_probe_is_deterministic():
    assert run_world_model_probe(seed=7) == run_world_model_probe(seed=7)


def test_world_model_reports_rollout_and_planning():
    result = run_world_model_probe(seed=7)
    for name in ("lag-1", "lag-2"):
        model = result["models"][name]
        assert 0.0 <= model["rollout_accuracy"] <= 1.0
        assert isinstance(model["plan_success"], bool)
        assert model["training_examples"] > 0
