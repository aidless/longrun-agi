from longrun.benchmarks.clear_v1 import generate_clear_v1_tasks
from longrun.evaluation.protocol import (
    build_model_protocol,
    evaluate_model_response,
    run_model_protocol_dry_run,
)


def test_protocol_is_stable_and_keeps_test_split_sealed():
    tasks = generate_clear_v1_tasks(seed=20261028)
    first = build_model_protocol(tasks)
    second = build_model_protocol(tasks)
    assert first == second
    assert first["protocol_id"] == "clear-v1-model-eval-v1"
    assert first["splits"]["dry_run_allowed"] == ["train", "dev"]
    assert first["splits"]["test_status"] == "sealed-not-accessed"
    assert first["execution_contract"]["test_split_accessed"] is False
    assert len(first["protocol_sha256"]) == 64


def test_valid_fixture_passes_all_dry_run_tasks():
    result = run_model_protocol_dry_run()
    valid = result["policies"]["valid-fixture"]
    assert result["config"]["dry_run_tasks"] == 240
    assert result["config"]["test_tasks"] == 60
    assert valid["tasks"] == 240
    assert valid["successes"] == 240
    assert valid["success_rate"] == 1.0
    assert valid["valid_json_rate"] == 1.0
    assert valid["schema_valid_rate"] == 1.0
    assert valid["failure_counts"] == {}


def test_mixed_fixture_reports_failures_without_counting_success():
    result = run_model_protocol_dry_run()
    mixed = result["policies"]["mixed-failure-fixture"]
    assert mixed["successes"] < mixed["tasks"]
    assert mixed["valid_json_rate"] < 1.0
    assert mixed["schema_valid_rate"] < 1.0
    assert set(mixed["failure_counts"]) == {
        "timeout",
        "invalid-json",
        "wrong-output",
    }
    assert sum(mixed["failure_counts"].values()) + mixed["successes"] == 240
    assert result["test_split_status"] == "sealed-not-accessed"


def test_evaluator_rejects_malformed_schema_and_abstention():
    task = generate_clear_v1_tasks(seed=20261028)[0]
    assert evaluate_model_response(
        task, {"status": "invalid-json", "output": None}
    )["failure"] == "invalid-json"
    assert evaluate_model_response(
        task, {"status": "ok", "output": None}
    )["failure"] == "schema-invalid"
    assert evaluate_model_response(
        task,
        {"status": "ok", "output": {"unexpected": True}, "abstain": True},
    )["failure"] == "abstained"


def test_protocol_dry_run_is_deterministic():
    first = run_model_protocol_dry_run()
    second = run_model_protocol_dry_run()
    assert first == second
    assert first["status"] == "harness-validation"
    assert first["scientific_result"] is False
