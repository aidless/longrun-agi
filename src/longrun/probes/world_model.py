from __future__ import annotations

import random
from collections import defaultdict


def _sequence(seed: int, length: int = 600) -> list[int]:
    rng = random.Random(seed)
    outputs = [0, 1]
    while len(outputs) < length:
        previous = outputs[-1]
        delayed = outputs[-2] if len(outputs) >= 2 else 0
        noise = rng.randrange(10)
        if noise == 0:
            outputs.append(rng.randrange(4))
        else:
            outputs.append((previous + delayed * 2 + 1) % 4)
    return outputs


def _train_predictor(sequence: list[int], history: int) -> dict:
    counts: dict[tuple[int, ...], dict[int, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for index in range(history, len(sequence)):
        context = tuple(sequence[index - history : index])
        counts[context][sequence[index]] += 1
    correct = 0
    evaluated = 0
    for index in range(history, len(sequence)):
        context = tuple(sequence[index - history : index])
        prediction = max(counts[context], key=counts[context].get)
        correct += int(prediction == sequence[index])
        evaluated += 1
    return {
        "one_step_accuracy": correct / evaluated,
        "unique_contexts": len(counts),
        "training_examples": evaluated,
    }


def _rollout_accuracy(sequence: list[int], history: int) -> float:
    counts: dict[tuple[int, ...], dict[int, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for index in range(history, len(sequence)):
        context = tuple(sequence[index - history : index])
        counts[context][sequence[index]] += 1
    context = list(sequence[-history:])
    correct = 0
    total = 0
    for offset in range(history, min(history + 50, len(sequence))):
        prediction = max(counts[tuple(context)], key=counts[tuple(context)].get)
        correct += int(prediction == sequence[offset])
        total += 1
        context = (context + [prediction])[-history:]
    return correct / total


def _planner(sequence: list[int], history: int) -> dict:
    counts: dict[tuple[int, ...], dict[int, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for index in range(history, len(sequence)):
        context = tuple(sequence[index - history : index])
        counts[context][sequence[index]] += 1
    context = tuple(sequence[-history:])
    path = []
    for _ in range(8):
        if context not in counts:
            return {"plan_success": False, "path": path}
        prediction = max(counts[context], key=counts[context].get)
        path.append(prediction)
        context = (context + (prediction,))[-history:]
    return {"plan_success": True, "path": path}


def run_world_model_probe(*, seed: int = 20261028) -> dict:
    """Compare one-step and two-step context models on a deterministic stream."""
    sequence = _sequence(seed)
    split = int(len(sequence) * 0.7)
    train = sequence[:split]
    test = sequence[split:]
    models = {}
    for history, name in ((1, "lag-1"), (2, "lag-2")):
        trained = _train_predictor(train, history)
        counts: dict[tuple[int, ...], dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        for index in range(history, len(train)):
            context = tuple(train[index - history : index])
            counts[context][train[index]] += 1
        correct = 0
        evaluated = 0
        for index in range(history, len(test)):
            context = tuple(test[index - history : index])
            if context not in counts:
                prediction = 0
            else:
                prediction = max(counts[context], key=counts[context].get)
            correct += int(prediction == test[index])
            evaluated += 1
        models[name] = {
            "training_one_step_accuracy": trained["one_step_accuracy"],
            "one_step_accuracy": correct / evaluated,
            "unique_contexts": trained["unique_contexts"],
            "training_examples": trained["training_examples"],
            "test_examples": evaluated,
            "in_sample_rollout_accuracy": _rollout_accuracy(sequence, history),
            "rollout_accuracy": _rollout_accuracy(sequence, history),
            **_planner(sequence, history),
        }
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "config": {
            "seed": seed,
            "sequence_length": len(sequence),
            "alphabet_size": 4,
            "rollout_horizon": 50,
            "contexts": [1, 2],
            "train_test_split": 0.7,
        },
        "models": models,
        "notes": [
            "This is a symbolic next-symbol model, not a neural world model.",
            "The sequence includes deterministic delayed recurrence plus sparse noise.",
        ],
    }
