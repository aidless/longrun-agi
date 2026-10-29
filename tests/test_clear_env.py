import pytest

from longrun.clear.env import FileOpsEnv, normalize_path
from longrun.clear.generators import generate_tasks
from longrun.clear.models import Action, Op


def test_generator_has_paired_variants_and_complete_expected_state():
    tasks = generate_tasks(instances_per_variant=1)
    assert len(tasks) == 9
    families = {task.family_id for task in tasks}
    assert families == {"extension_sort", "prefix_route", "suffix_route"}
    for task in tasks:
        assert "docs/SPEC.md" in task.initial_files
        assert any(path.startswith("sorted/") for path in task.expected_files)
        assert not any(path.startswith("inbox/") for path in task.expected_files)


def test_path_traversal_is_rejected():
    with pytest.raises(ValueError):
        normalize_path("../outside")
    with pytest.raises(ValueError):
        normalize_path("/absolute")
    task = generate_tasks(instances_per_variant=1)[0]
    env = FileOpsEnv(task)
    observation = env.step(Action(Op.READ, path="../docs/SPEC.md"))
    assert not observation.ok
    assert "unsafe path" in observation.message


def test_list_and_read_are_read_only():
    task = generate_tasks(instances_per_variant=1)[0]
    env = FileOpsEnv(task)
    before = env.snapshot()
    listed = env.step(Action(Op.LIST, path="inbox"))
    assert listed.ok
    assert all(path.startswith("inbox/") for path in listed.value)
    read = env.step(Action(Op.READ, path="docs/SPEC.md"))
    assert read.ok
    assert "<RULE_JSON>" in read.value
    assert env.snapshot() == before
