from __future__ import annotations

import random
from statistics import fmean

from ..benchmarks.clear_v1 import generate_clear_v1_tasks


ACTIONS = ("retrieve", "reflect", "tool", "write-memory", "stop")
ACTION_COST = {
    "retrieve": 1,
    "reflect": 2,
    "tool": 3,
    "write-memory": 1,
    "stop": 0,
}
ACTION_TOKENS = {
    "retrieve": 120,
    "reflect": 260,
    "tool": 360,
    "write-memory": 100,
    "stop": 10,
}
ACTION_LATENCY_MS = {
    "retrieve": 90,
    "reflect": 180,
    "tool": 260,
    "write-memory": 70,
    "stop": 5,
}


def _clip(value: float) -> float:
    return max(0.02, min(0.98, value))


def _state(task) -> tuple[str, int, str]:
    # Training only sees variants 0-2; the controller uses a coarse bucket so
    # dev/test variants remain representable without leaking their labels.
    return task.environment, int(task.variant >= 2), task.family_id


def _base_probability(task) -> float:
    environment_base = {
        "filesystem": 0.58,
        "browser": 0.52,
        "gridworld": 0.46,
    }[task.environment]
    family_offset = (sum(ord(char) for char in task.family_id) % 7 - 3) * 0.008
    return _clip(environment_base + family_offset - task.variant * 0.025)


def _probability(task, action: str, memory_bonus: int) -> float:
    probability = _base_probability(task)
    if action == "retrieve":
        probability += {
            "filesystem": 0.06,
            "browser": 0.14,
            "gridworld": 0.02,
        }[task.environment]
    elif action == "reflect":
        probability += 0.22 if task.variant >= 2 else 0.05
    elif action == "tool":
        probability += {
            "filesystem": 0.20,
            "browser": 0.10,
            "gridworld": 0.04,
        }[task.environment]
    elif action == "write-memory":
        probability += 0.06
    if memory_bonus > 0:
        probability += min(0.10, 0.025 * memory_bonus)
    return _clip(probability)


def _argmax(values: list[float]) -> int:
    return max(range(len(values)), key=lambda index: (values[index], -index))


def _train(
    *,
    seed: int,
    train_episodes: int,
) -> tuple[dict, dict]:
    tasks = [
        task
        for task in generate_clear_v1_tasks(seed=seed)
        if task.split == "train"
    ]
    rng = random.Random(seed)
    q: dict[tuple[str, int, str], list[float]] = {}
    outcomes: dict[tuple[tuple[str, int, str], str], list[int]] = {}
    memory_bonus: dict[str, int] = {}
    for _ in range(train_episodes):
        task = rng.choice(tasks)
        state = _state(task)
        values = q.setdefault(state, [0.0] * len(ACTIONS))
        if rng.random() < 0.22:
            action_index = rng.randrange(len(ACTIONS))
        else:
            action_index = _argmax(values)
        action = ACTIONS[action_index]
        probability = _probability(
            task,
            action,
            memory_bonus.get(task.family_id, 0),
        )
        success = rng.random() < probability
        reward = float(success) - 0.04 * ACTION_COST[action]
        values[action_index] += 0.16 * (reward - values[action_index])
        outcomes.setdefault((state, action), []).append(int(success))
        if action == "write-memory":
            memory_bonus[task.family_id] = 5
        else:
            current = memory_bonus.get(task.family_id, 0)
            if current > 0:
                memory_bonus[task.family_id] = current - 1
    return q, outcomes


def _predicted_success(
    outcomes: dict[tuple[tuple[str, int, str], str], list[int]],
    state: tuple[str, int, str],
    action: str,
) -> float:
    values = outcomes.get((state, action), [])
    return fmean(values) if values else 0.5


def _ece(rows: list[tuple[float, bool]]) -> float:
    bins = [{"confidence": 0.0, "correct": 0.0, "count": 0} for _ in range(5)]
    for confidence, correct in rows:
        index = min(4, int(confidence * 5))
        bins[index]["confidence"] += confidence
        bins[index]["correct"] += float(correct)
        bins[index]["count"] += 1
    total = len(rows)
    return sum(
        abs(
            bucket["confidence"] / bucket["count"]
            - bucket["correct"] / bucket["count"]
        )
        * bucket["count"]
        / total
        for bucket in bins
        if bucket["count"]
    )


def _evaluate(
    *,
    policy_name: str,
    tasks: list,
    q: dict | None,
    outcomes: dict,
    seed: int,
    blocks: int = 5,
) -> dict:
    rng = random.Random(seed)
    rows = []
    action_counts = {action: 0 for action in ACTIONS}
    memory_bonus: dict[str, int] = {}
    block_successes = []
    for block in range(blocks):
        block_tasks = tasks[block::blocks]
        successes = 0
        for task in block_tasks:
            state = _state(task)
            if policy_name == "adaptive":
                action = ACTIONS[_argmax(q.get(state, [0.0] * len(ACTIONS)))]
            else:
                action = policy_name
            probability = _probability(
                task,
                action,
                memory_bonus.get(task.family_id, 0),
            )
            success = rng.random() < probability
            successes += int(success)
            action_counts[action] += 1
            rows.append(
                {
                    "state": state,
                    "action": action,
                    "success": success,
                    "cost": ACTION_COST[action],
                    "tokens": ACTION_TOKENS[action],
                    "latency": ACTION_LATENCY_MS[action],
                    "predicted": _predicted_success(outcomes, state, action),
                }
            )
            if action == "write-memory":
                memory_bonus[task.family_id] = 5
            else:
                current = memory_bonus.get(task.family_id, 0)
                if current > 0:
                    memory_bonus[task.family_id] = current - 1
        block_successes.append(
            successes / len(block_tasks) if block_tasks else 0.0
        )
    successes = sum(row["success"] for row in rows)
    return {
        "tasks": len(rows),
        "successes": successes,
        "success_rate": successes / len(rows),
        "mean_cost": fmean(row["cost"] for row in rows),
        "cost_per_success": (
            fmean(row["cost"] for row in rows) / (successes / len(rows))
            if successes
            else float("inf")
        ),
        "mean_token_proxy": fmean(row["tokens"] for row in rows),
        "mean_latency_ms": fmean(row["latency"] for row in rows),
        "calibration_error": _ece(
            [(row["predicted"], row["success"]) for row in rows]
        ),
        "stability_range": max(block_successes) - min(block_successes),
        "block_success_rates": block_successes,
        "action_counts": action_counts,
        "memory_writes": action_counts["write-memory"],
    }


def run_adaptive_controller_probe(
    *,
    seed: int = 20261028,
    train_episodes: int = 600,
) -> dict:
    if train_episodes < 1:
        raise ValueError("train_episodes must be positive")
    q, outcomes = _train(seed=seed, train_episodes=train_episodes)
    tasks = [
        task
        for task in generate_clear_v1_tasks(seed=seed)
        if task.split in ("dev", "test")
    ]
    policies = {}
    for action in ACTIONS:
        policies[action] = _evaluate(
            policy_name=action,
            tasks=tasks,
            q=None,
            outcomes=outcomes,
            seed=seed + 500,
        )
    policies["adaptive"] = _evaluate(
        policy_name="adaptive",
        tasks=tasks,
        q=q,
        outcomes=outcomes,
        seed=seed + 500,
    )
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "scope": "synthetic contextual bandit on CLEAR-300-v1 metadata; no model or API",
        "config": {
            "seed": seed,
            "train_episodes": train_episodes,
            "evaluation_tasks": len(tasks),
            "actions": list(ACTIONS),
            "cost_weights": ACTION_COST,
        },
        "policies": policies,
        "notes": [
            "Outcomes are synthetic and driven by environment, variant, family, and action.",
            "Token and latency values are proxy costs, not measured hardware or model usage.",
            "The controller is a tabular contextual bandit, not a runtime model controller.",
        ],
    }
