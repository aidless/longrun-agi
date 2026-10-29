import pytest

from longrun.clear.generators import (
    generate_factorial_tasks,
    generate_fault_tasks,
    generate_tasks,
    generate_three_factor_tasks,
)
from longrun.clear.policies import (
    ConfigurableSpecPolicy,
    MemorySpecPolicy,
    PolicyError,
    ReactiveSpecPolicy,
    StickySpecPolicy,
)
from longrun.clear.runner import evaluate, factorial_effects, run_episode


def test_reactive_policy_passes_all_rule_shifts():
    tasks = generate_tasks(instances_per_variant=1)
    result = evaluate(tasks, ReactiveSpecPolicy, "reactive-spec")
    assert result["overall"]["success_rate"] == 1.0
    assert result["overall"]["shift_success_rate"] == 1.0


def test_evaluate_creates_one_policy_for_each_family():
    tasks = generate_tasks(instances_per_variant=1)
    policies = []

    def factory():
        policy = ReactiveSpecPolicy()
        policies.append(policy)
        return policy

    evaluate(tasks, factory, "reactive-spec")
    assert len(policies) == 3


def test_evaluate_sorts_tasks_within_each_family():
    tasks = list(reversed(generate_tasks(instances_per_variant=1)))
    result = evaluate(tasks, ReactiveSpecPolicy, "reactive-spec")
    observed = [
        (row["family_id"], row["variant"], row["task_id"])
        for row in result["results"]
    ]
    expected = sorted(
        (task.family_id, task.variant, task.task_id) for task in tasks
    )
    assert observed == expected


def test_sticky_policy_passes_base_and_fails_shifted_variants():
    tasks = generate_tasks(instances_per_variant=1)
    result = evaluate(tasks, StickySpecPolicy, "sticky-spec")
    assert result["overall"]["base_success_rate"] == 1.0
    assert result["overall"]["shift_success_rate"] == 0.0


def test_sticky_policy_retains_rule_across_episodes():
    base = next(
        task
        for task in generate_tasks(instances_per_variant=1)
        if task.family_id == "extension_sort" and task.variant == 0
    )
    shifted = next(
        task
        for task in generate_tasks(instances_per_variant=1)
        if task.family_id == "extension_sort" and task.variant == 1
    )
    policy = StickySpecPolicy()
    assert run_episode(base, policy).success is True
    assert policy.mode == "extension"
    assert run_episode(shifted, policy).success is False


def test_reset_clears_episode_state_and_only_retains_declared_rule():
    base = next(
        task
        for task in generate_tasks(instances_per_variant=1)
        if task.family_id == "extension_sort" and task.variant == 0
    )
    sticky = StickySpecPolicy()
    run_episode(base, sticky)
    sticky.pending = ["inbox/unfinished.txt"]
    sticky.phase = "moving"

    sticky.reset()

    assert sticky.mode == "extension"
    assert sticky.mapping
    assert sticky.pending == []
    assert sticky.current_move is None
    assert sticky.phase == "start"

    reactive = ReactiveSpecPolicy()
    run_episode(base, reactive)
    reactive.reset()
    assert reactive.mode is None
    assert reactive.mapping == {}


def test_runner_resets_state_after_policy_exception():
    class FailOncePolicy:
        name = "fail-once"

        def __init__(self):
            self.delegate = ReactiveSpecPolicy()
            self.fail_next = True

        def reset(self):
            self.delegate.reset()

        def act(self, observation):
            if self.fail_next:
                self.fail_next = False
                raise PolicyError("deliberate one-shot failure")
            return self.delegate.act(observation)

    task = next(
        task
        for task in generate_tasks(instances_per_variant=1)
        if task.family_id == "extension_sort" and task.variant == 0
    )
    policy = FailOncePolicy()
    failed = run_episode(task, policy)
    recovered = run_episode(task, policy)

    assert failed.success is False
    assert failed.error == "PolicyError: deliberate one-shot failure"
    assert recovered.success is True


def test_memory_policy_resets_routing_state_for_every_episode():
    class RecordingMemoryPolicy(MemorySpecPolicy):
        def __init__(self):
            super().__init__(trusted_memory=True)
            self.reset_states = []

        def reset(self):
            super().reset()
            self.reset_states.append(
                (self.mode, dict(self.mapping), list(self.pending), self.phase)
            )

    tasks = [
        task
        for task in generate_three_factor_tasks(instances_per_variant=1)
        if task.family_id == "three_factor_extension_sort"
        and task.metadata["tool_fault"] == 0
    ][:2]
    assert len(tasks) == 2
    policy = RecordingMemoryPolicy()

    first = run_episode(tasks[0], policy)
    second = run_episode(tasks[1], policy)

    assert first.success is True
    assert second.success is True
    assert policy.reset_states == [
        (None, {}, [], "start"),
        (None, {}, [], "start"),
    ]


def test_reference_policy_recovers_from_transient_faults():
    tasks = generate_fault_tasks()
    result = evaluate(tasks, ReactiveSpecPolicy, "reactive-spec")
    assert result["overall"]["faulted_runs"] == 2
    assert result["overall"]["faulted_recovery_rate"] == 1.0
    assert all(row["faults_injected"] for row in result["results"])


def test_factorial_generator_has_complete_crossed_cells():
    tasks = generate_factorial_tasks(instances_per_variant=1)
    assert len(tasks) == 12
    keys = {
        (task.metadata["rule_shift"], task.metadata["tool_fault"])
        for task in tasks
    }
    assert keys == {(0, 0), (0, 1), (1, 0), (1, 1)}
    assert all(
        len([task for task in tasks if task.metadata["rule_shift"] == rule_shift
             and task.metadata["tool_fault"] == tool_fault]) == 3
        for rule_shift in (0, 1)
        for tool_fault in (0, 1)
    )


def test_factorial_robust_policy_passes_all_cells():
    tasks = generate_factorial_tasks(instances_per_variant=1)
    result = evaluate(
        tasks,
        lambda: ConfigurableSpecPolicy(retain_rule=False, retry_on_error=True),
        "robust",
    )
    effects = factorial_effects(result)
    assert result["overall"]["successes"] == len(tasks)
    assert effects["rule_shift_main_effect"] == 0.0
    assert effects["tool_fault_main_effect"] == 0.0
    assert effects["interaction_rule_x_tool"] == 0.0


def test_factorial_no_retry_isolates_tool_fault_effect():
    tasks = generate_factorial_tasks(instances_per_variant=1)
    result = evaluate(
        tasks,
        lambda: ConfigurableSpecPolicy(retain_rule=False, retry_on_error=False),
        "no-retry",
    )
    effects = factorial_effects(result)
    assert effects["rule_shift_main_effect"] == 0.0
    assert effects["tool_fault_main_effect"] == 1.0


def test_factorial_sticky_rule_isolates_rule_shift_effect():
    tasks = generate_factorial_tasks(instances_per_variant=1)
    result = evaluate(
        tasks,
        lambda: ConfigurableSpecPolicy(retain_rule=True, retry_on_error=True),
        "sticky-rule",
    )
    effects = factorial_effects(result)
    assert effects["rule_shift_main_effect"] == 1.0


def test_factorial_fragile_policy_shows_both_failure_factors():
    tasks = generate_factorial_tasks(instances_per_variant=1)
    result = evaluate(
        tasks,
        lambda: ConfigurableSpecPolicy(retain_rule=True, retry_on_error=False),
        "fragile",
    )
    effects = factorial_effects(result)
    assert effects["rule_shift_main_effect"] == 0.5
    assert effects["tool_fault_main_effect"] == 0.5
    assert effects["interaction_rule_x_tool"] == 1.0


def test_three_factor_generator_has_all_eight_cells():
    tasks = generate_three_factor_tasks(instances_per_variant=1)
    assert len(tasks) == 24
    keys = {
        tuple(
            task.metadata[name]
            for name in ("rule_shift", "tool_fault", "memory_poison")
        )
        for task in tasks
    }
    assert len(keys) == 8
    assert all(
        sum(
            task.metadata["rule_shift"] == rule_shift
            and task.metadata["tool_fault"] == tool_fault
            and task.metadata["memory_poison"] == memory_poison
            for task in tasks
        ) == 3
        for rule_shift in (0, 1)
        for tool_fault in (0, 1)
        for memory_poison in (0, 1)
    )


def test_memory_naive_policy_tracks_poisoned_note():
    tasks = generate_three_factor_tasks(instances_per_variant=1)
    result = evaluate(
        tasks,
        lambda: MemorySpecPolicy(trusted_memory=False),
        "memory-naive",
    )
    effects = factorial_effects(result)
    assert effects["main_effects"]["memory_poison"] == 1.0
    assert effects["main_effects"]["rule_shift"] == 0.0
    assert effects["main_effects"]["tool_fault"] == 0.0


def test_memory_provenance_policy_rejects_poisoned_note():
    tasks = generate_three_factor_tasks(instances_per_variant=1)
    result = evaluate(
        tasks,
        lambda: MemorySpecPolicy(trusted_memory=True),
        "memory-provenance",
    )
    effects = factorial_effects(result)
    assert effects["main_effects"] == {
        "memory_poison": 0.0,
        "rule_shift": 0.0,
        "tool_fault": 0.0,
    }
    assert all(
        abs(value) == 0.0 for value in effects["interactions"].values()
    )


def test_three_factor_interaction_contrast_is_computed_from_all_cells():
    successes = {
        (0, 0, 0): 1.0,
        (0, 0, 1): 0.0,
        (0, 1, 0): 0.0,
        (0, 1, 1): 1.0,
        (1, 0, 0): 0.0,
        (1, 0, 1): 1.0,
        (1, 1, 0): 1.0,
        (1, 1, 1): 0.0,
    }
    result = {
        "results": [
            {
                "task_id": f"cell-{rule}-{tool}-{memory}",
                "factors": {
                    "rule_shift": rule,
                    "tool_fault": tool,
                    "memory_poison": memory,
                },
                "success": success,
            }
            for (rule, tool, memory), success in successes.items()
        ]
    }
    effects = factorial_effects(result)
    assert effects["main_effects"] == {
        "rule_shift": 0.0,
        "tool_fault": 0.0,
        "memory_poison": 0.0,
    }
    assert effects["interactions"][
        "rule_shift_x_tool_fault_x_memory_poison"
    ] == 4.0
