import json

from longrun.benchmarks.clear_v1 import (
    build_split_manifest,
    generate_clear_v1_tasks,
    run_scripted_baselines,
    task_record,
    verify_task,
)


def test_clear_v1_has_300_frozen_shape_tasks():
    tasks = generate_clear_v1_tasks(seed=20261028)
    assert len(tasks) == 300
    assert len({task.task_id for task in tasks}) == 300
    assert {task.environment for task in tasks} == {
        "filesystem",
        "browser",
        "gridworld",
    }
    for environment in ("filesystem", "browser", "gridworld"):
        assert sum(task.environment == environment for task in tasks) == 100
    assert sum(task.split == "train" for task in tasks) == 180
    assert sum(task.split == "dev" for task in tasks) == 60
    assert sum(task.split == "test" for task in tasks) == 60
    assert all(task.variant in range(5) for task in tasks)
    assert all(task.family_id for task in tasks)


def test_clear_v1_is_deterministic_and_has_serializable_records():
    first = generate_clear_v1_tasks(seed=20261028)
    second = generate_clear_v1_tasks(seed=20261028)
    assert [task_record(task) for task in first] == [
        task_record(task) for task in second
    ]
    json.dumps([task_record(task) for task in first], sort_keys=True)


def test_clear_v1_every_task_has_a_valid_current_rule_solution():
    tasks = generate_clear_v1_tasks(seed=20261028)
    assert all(verify_task(task) for task in tasks)


def test_clear_v1_sticky_baseline_exposes_rule_shift_failure():
    tasks = generate_clear_v1_tasks(seed=20261028)
    baselines = run_scripted_baselines(tasks)
    assert baselines["current-rule"]["success_rate"] == 1.0
    assert baselines["sticky-first-rule"]["success_rate"] < 1.0
    assert (
        baselines["sticky-first-rule"]["by_environment"]["filesystem"][
            "success_rate"
        ]
        < 1.0
    )
    assert (
        baselines["sticky-first-rule"]["by_environment"]["browser"][
            "success_rate"
        ]
        < 1.0
    )
    assert (
        baselines["sticky-first-rule"]["by_environment"]["gridworld"][
            "success_rate"
        ]
        < 1.0
    )


def test_split_manifest_contains_hashes_and_counts():
    tasks = generate_clear_v1_tasks(seed=20261028)
    manifest = build_split_manifest(tasks, seed=20261028)
    assert manifest["name"] == "clear-300-v1"
    assert manifest["counts"]["total"] == 300
    assert manifest["splits"] == {"train": 180, "dev": 60, "test": 60}
    assert len(manifest["tasks"]) == 300
    assert all(
        len(task["task_sha256"]) == 64 for task in manifest["tasks"]
    )
    assert len(manifest["canonical_sha256"]) == 64
