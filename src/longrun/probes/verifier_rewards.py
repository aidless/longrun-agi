from __future__ import annotations

import math
import random
from dataclasses import dataclass
from statistics import fmean


@dataclass(frozen=True, slots=True)
class _Task:
    family: str
    difficulty: int
    verifier_bucket: int
    short_success: float
    reason_success: float
    verifier_short: float
    verifier_reason: float
    ood: bool


def _clip(value: float) -> float:
    return max(0.0, min(1.0, value))


def _make_task(rng: random.Random, *, ood: bool) -> _Task:
    family = rng.choice(("math", "code", "planning"))
    difficulty = rng.randrange(2)
    if family == "math":
        short = 0.65
        reason = 0.88
    elif family == "code":
        short = 0.54
        reason = 0.82
    else:
        short = 0.42
        reason = 0.74
    if difficulty:
        short -= 0.08
        reason -= 0.05
    if ood:
        short -= 0.28
        reason -= 0.08
    short = _clip(short + rng.uniform(-0.10, 0.10))
    reason = _clip(reason + rng.uniform(-0.10, 0.10))
    verifier_short = _clip(short + rng.uniform(-0.14, 0.20))
    verifier_reason = _clip(reason + rng.uniform(-0.10, 0.14))
    return _Task(
        family=family,
        difficulty=difficulty,
        verifier_bucket=min(2, int(verifier_short * 3)),
        short_success=short,
        reason_success=reason,
        verifier_short=verifier_short,
        verifier_reason=verifier_reason,
        ood=ood,
    )


def _state(task: _Task) -> tuple[str, int, int]:
    return task.family, task.difficulty, task.verifier_bucket


def _action_name(index: int) -> str:
    return "shortcut" if index == 0 else "reason"


def _execute(task: _Task, action: int, rng: random.Random) -> dict:
    success_probability = task.short_success if action == 0 else task.reason_success
    success = rng.random() < success_probability
    self_signal = (
        task.verifier_short if action == 0 else task.verifier_reason
    ) + rng.uniform(-0.15, 0.15)
    return {
        "action": _action_name(action),
        "success": success,
        "self_signal": _clip(self_signal),
        "cost": 0 if action == 0 else 2,
        "failure": not success,
    }


def _reward(mode: str, task: _Task, result: dict) -> float:
    success = float(result["success"])
    action = result["action"]
    if mode == "answer":
        return success
    if mode == "process":
        return success + (0.35 if action == "reason" else 0.0)
    if mode == "self-verification":
        return result["self_signal"] - 0.05 * result["cost"]
    if mode == "ensemble-disagreement":
        consensus = (
            1.0
            if task.verifier_short >= 0.55 and task.verifier_reason >= 0.55
            else 0.0
        )
        disagreement = abs(task.verifier_short - task.verifier_reason)
        return (
            success
            + 0.20 * consensus
            - 0.40 * disagreement
            - 0.05 * result["cost"]
        )
    raise ValueError(f"unknown reward mode: {mode}")


def _argmax(values: tuple[float, float]) -> int:
    return 0 if values[0] >= values[1] else 1


def _train_policy(
    mode: str,
    *,
    seed: int,
    episodes: int,
) -> tuple[dict, dict, random.Random]:
    rng = random.Random(seed)
    q: dict[tuple[str, int, int], list[float]] = {}
    outcomes: dict[tuple[tuple[str, int, int], str], list[int]] = {}
    for _ in range(episodes):
        task = _make_task(rng, ood=False)
        state = _state(task)
        values = q.setdefault(state, [0.0, 0.0])
        if rng.random() < 0.22:
            action = rng.randrange(2)
        else:
            action = _argmax(tuple(values))
        result = _execute(task, action, rng)
        reward = _reward(mode, task, result)
        values[action] += 0.18 * (
            reward - values[action]
        )
        key = (state, result["action"])
        outcomes.setdefault(key, []).append(int(result["success"]))
    return q, outcomes, rng


def _predict_success(
    outcomes: dict[tuple[tuple[str, int, int], str], list[int]],
    state: tuple[str, int, int],
    action: str,
) -> float:
    values = outcomes.get((state, action), [])
    return fmean(values) if values else 0.5


def _ece(
    rows: list[tuple[float, bool]]
) -> float:
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
    q: dict[tuple[str, int, int], list[float]],
    outcomes: dict[tuple[tuple[str, int, int], str], list[int]],
    *,
    seed: int,
    episodes: int,
    ood: bool,
) -> dict:
    rng = random.Random(seed + (1 if ood else 0))
    rows = []
    success = 0
    costs = 0
    hacking = 0
    shortcut_count = 0
    reason_count = 0
    calibration_rows = []
    for _ in range(episodes):
        task = _make_task(rng, ood=ood)
        state = _state(task)
        action = _argmax(tuple(q.get(state, [0.0, 0.0])))
        result = _execute(task, action, rng)
        success += int(result["success"])
        costs += result["cost"]
        if result["action"] == "shortcut":
            shortcut_count += 1
            if not result["success"] and task.verifier_short >= 0.65:
                hacking += 1
        else:
            reason_count += 1
        predicted = _predict_success(outcomes, state, result["action"])
        calibration_rows.append((predicted, result["success"]))
        rows.append(result)
    return {
        "tasks": episodes,
        "successes": success,
        "success_rate": success / episodes,
        "mean_reasoning_cost": costs / episodes,
        "shortcut_rate": shortcut_count / episodes,
        "reasoning_rate": reason_count / episodes,
        "reward_hacking_rate": hacking / max(1, shortcut_count),
        "reward_hacking_events": hacking,
        "calibration_error": _ece(calibration_rows),
    }


def run_verifier_reward_probe(
    *,
    seed: int = 20261028,
    train_episodes: int = 600,
) -> dict:
    if train_episodes < 1:
        raise ValueError("train_episodes must be positive")
    policies = {}
    for mode in (
        "answer",
        "process",
        "self-verification",
        "ensemble-disagreement",
    ):
        q, outcomes, _ = _train_policy(
            mode,
            seed=seed,
            episodes=train_episodes,
        )
        id_result = _evaluate(
            q,
            outcomes,
            seed=seed + 100,
            episodes=300,
            ood=False,
        )
        ood_result = _evaluate(
            q,
            outcomes,
            seed=seed + 100,
            episodes=300,
            ood=True,
        )
        policies[mode] = {
            "id_success_rate": id_result["success_rate"],
            "ood_success_rate": ood_result["success_rate"],
            "ood_transfer_drop": id_result["success_rate"]
            - ood_result["success_rate"],
            "id_calibration_error": id_result["calibration_error"],
            "ood_calibration_error": ood_result["calibration_error"],
            "id_reward_hacking_rate": id_result["reward_hacking_rate"],
            "ood_reward_hacking_rate": ood_result["reward_hacking_rate"],
            "reward_hacking_rate": fmean(
                [
                    id_result["reward_hacking_rate"],
                    ood_result["reward_hacking_rate"],
                ]
            ),
            "mean_reasoning_cost": fmean(
                [
                    id_result["mean_reasoning_cost"],
                    ood_result["mean_reasoning_cost"],
                ]
            ),
            "id_reasoning_rate": id_result["reasoning_rate"],
            "ood_reasoning_rate": ood_result["reasoning_rate"],
            "id_shortcut_rate": id_result["shortcut_rate"],
            "ood_shortcut_rate": ood_result["shortcut_rate"],
        }
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "scope": "tabular synthetic reward protocol; no language model",
        "config": {
            "seed": seed,
            "train_episodes": train_episodes,
            "evaluation_episodes": 300,
            "families": ["math", "code", "planning"],
            "actions": ["shortcut", "reason"],
        },
        "policies": policies,
        "notes": [
            "Verifier signals are synthetic and observable through a bucket.",
            "Answer, process, self-verification, and ensemble rewards are compared under the same task distribution.",
            "This is a protocol check, not Qwen/Llama training or a real reward-hacking result.",
        ],
    }
