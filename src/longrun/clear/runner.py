from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Callable, Iterable

from .env import FileOpsEnv
from .models import Observation
from .models import Task


@dataclass(frozen=True, slots=True)
class EpisodeResult:
    task_id: str
    family_id: str
    variant: int
    policy: str
    success: bool
    steps: int
    tool_failures: int
    faults_injected: tuple[str, ...]
    final_digest: str
    final_file_count: int
    error: str | None
    factors: dict[str, int]


def _task_factors(task: Task) -> dict[str, int]:
    names = ("rule_shift", "tool_fault", "memory_poison")
    return {
        name: int(task.metadata[name])
        for name in names
        if name in task.metadata
    }


def run_episode(task: Task, policy) -> EpisodeResult:
    policy.reset()
    env = FileOpsEnv(task)
    observation = Observation(ok=True, message="start", step=0, done=False)
    error: str | None = None
    for _ in range(task.max_steps + 2):
        try:
            action = policy.act(observation)
            observation = env.step(action)
        except Exception as exc:  # preserve policy failures instead of hiding them
            error = f"{type(exc).__name__}: {exc}"
            break
        if observation.done:
            break

    success = env.is_success()
    if error is not None:
        success = False
    return EpisodeResult(
        task_id=task.task_id,
        family_id=task.family_id,
        variant=task.variant,
        policy=getattr(policy, "name", type(policy).__name__),
        success=success,
        steps=env.step_count,
        tool_failures=len(env.faults_injected),
        faults_injected=tuple(env.faults_injected),
        final_digest=env.state_digest(),
        final_file_count=len(env.files),
        error=error or (None if success else observation.message),
        factors=_task_factors(task),
    )


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def summarize(results: list[EpisodeResult]) -> dict:
    base = [result for result in results if result.variant == 0]
    shifted = [result for result in results if result.variant > 0]
    faulted = [result for result in results if result.faults_injected]
    return {
        "runs": len(results),
        "successes": sum(result.success for result in results),
        "success_rate": _mean([float(result.success) for result in results]),
        "base_success_rate": _mean([float(result.success) for result in base]),
        "shift_success_rate": _mean([float(result.success) for result in shifted]),
        "mean_steps": _mean([float(result.steps) for result in results]),
        "faulted_runs": len(faulted),
        "faulted_recoveries": sum(
            result.success for result in faulted
        ),
        "faulted_recovery_rate": _mean(
            [float(result.success) for result in faulted]
        ),
    }


def evaluate(
    tasks: Iterable[Task],
    policy_factory: Callable[[], object],
    policy_name: str,
) -> dict:
    grouped: dict[str, list[Task]] = defaultdict(list)
    for task in tasks:
        grouped[task.family_id].append(task)

    results: list[EpisodeResult] = []
    family_summaries: dict[str, dict] = {}
    for family_id in sorted(grouped):
        policy = policy_factory()
        family_results: list[EpisodeResult] = []
        for task in sorted(grouped[family_id], key=lambda item: (item.variant, item.task_id)):
            family_results.append(run_episode(task, policy))
        results.extend(family_results)
        family_summaries[family_id] = summarize(family_results)

    payload = {
        "policy": policy_name,
        "overall": summarize(results),
        "families": family_summaries,
        "results": [asdict(result) for result in results],
    }
    return payload


def factorial_effects(policy_result: dict) -> dict:
    """Estimate balanced 2-factor or 3-factor success contrasts."""
    rows = policy_result["results"]
    present_factors = {
        name
        for row in rows
        for name in row.get("factors", {})
    }
    canonical_order = ("rule_shift", "tool_fault", "memory_poison")
    factor_names = [name for name in canonical_order if name in present_factors]
    if not factor_names:
        # Backward-compatible fallback for the first 2x2 output format.
        factor_names = ["rule_shift", "tool_fault"]
    for row in rows:
        factors = row.get("factors") or {
            "rule_shift": int("rs1" in row["task_id"]),
            "tool_fault": int("tf1" in row["task_id"]),
        }
        if any(name not in factors for name in factor_names):
            raise ValueError(f"result row lacks one of the factors: {factors!r}")
    expected_factors = {"rule_shift", "tool_fault", "memory_poison"}
    if not set(factor_names).issubset(expected_factors):
        raise ValueError(f"unsupported factor set: {factor_names!r}")
    if len(factor_names) not in {2, 3}:
        raise ValueError(f"expected 2 or 3 factors, got {factor_names!r}")

    short = {
        "rule_shift": "rs",
        "tool_fault": "tf",
        "memory_poison": "mp",
    }
    cells: dict[tuple[int, ...], list[float]] = defaultdict(list)
    for row in rows:
        factors = row.get("factors") or {
            "rule_shift": int("rs1" in row["task_id"]),
            "tool_fault": int("tf1" in row["task_id"]),
        }
        levels = tuple(factors[name] for name in factor_names)
        cells[levels].append(float(row["success"]))
    cell_success = {
        "_".join(
            f"{short[name]}{level}"
            for name, level in zip(factor_names, levels)
        ): _mean(values)
        for levels, values in sorted(cells.items())
    }

    def mean_for(**conditions: int) -> float:
        values = [
            float(row["success"])
            for row in rows
            if all(
                (row.get("factors") or {}).get(name) == level
                or (
                    not row.get("factors")
                    and (
                        (name == "rule_shift" and level == int("rs1" in row["task_id"]))
                        or (name == "tool_fault" and level == int("tf1" in row["task_id"]))
                    )
                )
                for name, level in conditions.items()
            )
        ]
        if not values:
            raise ValueError(f"empty factorial cell: {conditions!r}")
        return sum(values) / len(values)

    main_effects = {
        name: mean_for(**{name: 0}) - mean_for(**{name: 1})
        for name in factor_names
    }
    interactions: dict[str, float] = {}
    for first_index, first in enumerate(factor_names):
        for second in factor_names[first_index + 1 :]:
            interactions[f"{first}_x_{second}"] = (
                mean_for(**{first: 0, second: 0})
                - mean_for(**{first: 1, second: 0})
                - mean_for(**{first: 0, second: 1})
                + mean_for(**{first: 1, second: 1})
            )
    if len(factor_names) == 3:
        first, second, third = factor_names

        def pair_at_third(level: int) -> float:
            return (
                mean_for(**{first: 0, second: 0, third: level})
                - mean_for(**{first: 1, second: 0, third: level})
                - mean_for(**{first: 0, second: 1, third: level})
                + mean_for(**{first: 1, second: 1, third: level})
            )

        interactions[f"{first}_x_{second}_x_{third}"] = (
            pair_at_third(0) - pair_at_third(1)
        )
    else:
        first, second = factor_names

    payload = {
        "factors": factor_names,
        "cell_success": cell_success,
        "main_effects": main_effects,
        "interactions": interactions,
    }
    if len(factor_names) == 2:
        payload.update(
            {
                "rule_shift_main_effect": main_effects[first],
                "tool_fault_main_effect": main_effects[second],
                "interaction_rule_x_tool": interactions[f"{first}_x_{second}"],
            }
        )
    return payload
