from longrun.clear.second_generator import (
    generate_second_clear_tasks,
    generate_second_factorial_tasks,
)
from longrun.clear.policies import ReactiveSpecPolicy, StickySpecPolicy
from longrun.clear.runner import evaluate


def test_second_generator_is_deterministic_and_structurally_distinct():
    first = generate_second_clear_tasks(instances_per_variant=2, seed=17)
    second = generate_second_clear_tasks(instances_per_variant=2, seed=17)
    assert first == second
    assert len(first) == 12
    assert len({task.family_id for task in first}) == 3
    assert {task.metadata["generator"] for task in first} == {"second-v0"}
    assert all(task.metadata["format"] == "named-list" for task in first)
    assert all("manifest/current.json" in task.initial_files for task in first)


def test_second_factorial_generator_crosses_all_cells():
    tasks = generate_second_factorial_tasks(instances_per_variant=4, seed=23)
    assert len(tasks) == 48
    cells = {}
    for task in tasks:
        key = (task.metadata["rule_shift"], task.metadata["tool_fault"])
        cells[key] = cells.get(key, 0) + 1
    assert cells == {(0, 0): 12, (0, 1): 12, (1, 0): 12, (1, 1): 12}


def test_second_generator_tasks_have_no_legacy_inbox_paths():
    tasks = generate_second_clear_tasks(instances_per_variant=1, seed=17)
    for task in tasks:
        assert all(not path.startswith("inbox/") for path in task.initial_files)
        assert any(path.startswith("queue/") for path in task.initial_files)


def test_existing_policies_can_run_second_generator_with_source_dir():
    tasks = generate_second_clear_tasks(instances_per_variant=1, seed=17)
    reactive = evaluate(
        tasks,
        lambda: ReactiveSpecPolicy(source_dir="queue"),
        "reactive-second",
    )
    assert reactive["overall"]["success_rate"] == 1.0


def test_second_generator_separates_sticky_policy():
    tasks = generate_second_clear_tasks(instances_per_variant=1, seed=17)
    sticky = evaluate(
        tasks,
        lambda: StickySpecPolicy(source_dir="queue"),
        "sticky-second",
    )
    assert sticky["overall"]["base_success_rate"] == 1.0
    assert sticky["overall"]["shift_success_rate"] < 1.0
