from __future__ import annotations

from dataclasses import replace

from .env import FileOpsEnv
from .generators import generate_factorial_tasks
from .models import Observation
from .policies import ConfigurableSpecPolicy


def run_cross_family_probe(*, seed: int = 20261028) -> dict:
    """Train a glued rule on one family and test it on another family."""
    if not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    directions = (
        ("extension_to_prefix", "extension_sort", "prefix_route"),
        ("prefix_to_suffix", "prefix_route", "suffix_route"),
        ("suffix_to_extension", "suffix_route", "extension_sort"),
    )
    tasks = generate_factorial_tasks(instances_per_variant=2)
    results = {}
    execution = {
        "policy_reused": True,
        "source_episodes_before_transfer": len(
            [
                task
                for task in tasks
                if task.family_id == "factorial_extension_sort"
                and task.metadata["tool_fault"] == 0
                and task.metadata["rule_shift"] == 0
            ]
        ),
    }
    for label, source, target in directions:
        source_tasks = [
            task
            for task in tasks
            if task.family_id == f"factorial_{source}"
            and task.metadata["tool_fault"] == 0
            and task.metadata["rule_shift"] == 0
        ]
        target_tasks = [
            task
            for task in tasks
            if task.family_id == f"factorial_{target}"
            and task.metadata["tool_fault"] == 0
            and task.metadata["rule_shift"] == 1
        ]
        policy = ConfigurableSpecPolicy(
            retain_rule=True,
            retry_on_error=True,
        )

        def run_episode(task) -> bool:
            policy.reset()
            env = FileOpsEnv(task)
            observation = Observation(True, "start", step=0, done=False)
            for _ in range(task.max_steps + 2):
                try:
                    observation = env.step(policy.act(observation))
                except Exception:
                    return False
                if observation.done:
                    break
            return env.is_success()

        train_successes = sum(run_episode(task) for task in source_tasks)
        transfer_successes = sum(run_episode(task) for task in target_tasks)
        train_rate = train_successes / len(source_tasks)
        transfer_rate = transfer_successes / len(target_tasks)
        results[label] = {
            "source_family": source,
            "target_family": target,
            "train_success": train_rate,
            "transfer_success": transfer_rate,
            "transfer_drop": train_rate - transfer_rate,
            "source_tasks": len(source_tasks),
            "target_tasks": len(target_tasks),
        }
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "seed": seed,
        "directions": results,
        "execution": execution,
        "notes": [
            "The probe tests whether a retained routing rule transfers across task families.",
            "A drop is expected when mode and mapping are incompatible; it is a harness check.",
        ],
    }
