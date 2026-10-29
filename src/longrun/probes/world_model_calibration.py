from __future__ import annotations

import itertools
import math
import random
from statistics import fmean


SYMBOLS = 4
ACTIONS = 4
TRAIN_STATES = (0, 1)
OOD_STATES = (2, 3)


def _true_next(state: int, action: int) -> int:
    return (state + action + 1) % SYMBOLS


def _table() -> list[list[int]]:
    return [[0 for _ in range(SYMBOLS)] for _ in range(ACTIONS)]


class _TableModel:
    def __init__(self) -> None:
        self.counts: dict[int, list[list[int]]] = {
            state: _table() for state in range(SYMBOLS)
        }

    def add(self, state: int, action: int, next_state: int) -> None:
        self.counts[state][action][next_state] += 1

    def predict(self, state: int, action: int) -> tuple[float, ...]:
        counts = self.counts[state][action]
        total = sum(counts)
        if total == 0:
            return tuple(1.0 / SYMBOLS for _ in range(SYMBOLS))
        return tuple((count + 0.5) / (total + 0.5 * SYMBOLS) for count in counts)


class _Ensemble:
    def __init__(self, models: tuple[_TableModel, _TableModel]) -> None:
        self.models = models

    def predict(self, state: int, action: int) -> tuple[float, ...]:
        first = self.models[0].predict(state, action)
        second = self.models[1].predict(state, action)
        return tuple((a + b) / 2.0 for a, b in zip(first, second))

    def disagreement(self, state: int, action: int) -> float:
        first = self.models[0].predict(state, action)
        second = self.models[1].predict(state, action)
        return sum(abs(a - b) for a, b in zip(first, second)) / 2.0

    def uncertainty(self, state: int, action: int) -> float:
        probabilities = self.predict(state, action)
        entropy = -sum(
            probability * math.log(probability)
            for probability in probabilities
            if probability > 0
        )
        normalized_entropy = entropy / math.log(SYMBOLS)
        return min(
            1.0,
            normalized_entropy + self.disagreement(state, action),
        )


def _samples(
    *,
    seed: int,
    states: tuple[int, ...],
    samples_per_pair: int,
    noise: float = 0.12,
) -> list[tuple[int, int, int]]:
    rng = random.Random(seed)
    rows = []
    for state in states:
        for action in range(ACTIONS):
            for _ in range(samples_per_pair):
                actual = _true_next(state, action)
                if rng.random() < noise:
                    actual = rng.randrange(SYMBOLS)
                rows.append((state, action, actual))
    return rows


def _split_models(rows: list[tuple[int, int, int]]) -> _Ensemble:
    first = _TableModel()
    second = _TableModel()
    for index, (state, action, actual) in enumerate(rows):
        (first if index % 2 == 0 else second).add(state, action, actual)
    return _Ensemble((first, second))


def _argmax(values: tuple[float, ...]) -> int:
    return max(range(len(values)), key=lambda index: (values[index], -index))


def _ece(
    rows: list[tuple[int, int]], model: _Ensemble
) -> float:
    bins = [{"confidence": 0.0, "correct": 0.0, "count": 0} for _ in range(5)]
    for state, action in rows:
        probabilities = model.predict(state, action)
        next_state = _true_next(state, action)
        confidence = max(probabilities)
        correct = _argmax(probabilities) == next_state
        index = min(4, int(confidence * 5))
        bins[index]["confidence"] += confidence
        bins[index]["correct"] += float(correct)
        bins[index]["count"] += 1
    total = len(rows)
    return sum(
        abs(
            (bucket["confidence"] / bucket["count"])
            - (bucket["correct"] / bucket["count"])
        )
        * bucket["count"]
        / total
        for bucket in bins
        if bucket["count"]
    )


def _auroc(rows: list[tuple[float, bool]]) -> float:
    positives = [score for score, label in rows if label]
    negatives = [score for score, label in rows if not label]
    if not positives or not negatives:
        return 0.5
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def _stats(rows: list[tuple[int, int]], model: _Ensemble) -> dict:
    correct = 0
    brier = 0.0
    uncertainties = []
    errors = []
    for state, action in rows:
        probabilities = model.predict(state, action)
        actual = _true_next(state, action)
        prediction = _argmax(probabilities)
        is_correct = prediction == actual
        correct += int(is_correct)
        brier += sum(
            (
                probability - (1.0 if index == actual else 0.0)
            )
            ** 2
            for index, probability in enumerate(probabilities)
        )
        uncertainty = model.uncertainty(state, action)
        uncertainties.append(uncertainty)
        errors.append((uncertainty, not is_correct))
    return {
        "samples": len(rows),
        "accuracy": correct / len(rows),
        "brier": brier / len(rows),
        "ece": _ece(rows, model),
        "mean_uncertainty": fmean(uncertainties),
        "uncertainty_error_auroc": _auroc(errors),
    }


def _counterfactual_error(model: _Ensemble, states: tuple[int, ...]) -> float:
    errors = []
    for state in states:
        for first_action in range(ACTIONS):
            for second_action in range(first_action + 1, ACTIONS):
                actual_delta = abs(
                    _true_next(state, first_action)
                    - _true_next(state, second_action)
                )
                predicted_delta = abs(
                    _argmax(model.predict(state, first_action))
                    - _argmax(model.predict(state, second_action))
                )
                errors.append(abs(actual_delta - predicted_delta))
    return fmean(errors)


def _rollout_error(
    model: _Ensemble,
    *,
    start: int,
    length: int = 12,
) -> float:
    state = start
    correct = 0
    for step in range(length):
        action = step % ACTIONS
        predicted = _argmax(model.predict(state, action))
        actual = _true_next(state, action)
        correct += int(predicted == actual)
        state = actual
    return 1.0 - correct / length


def _plan(
    model: _Ensemble,
    *,
    start: int,
    target: int,
    horizon: int,
    uncertainty_penalty: float,
) -> tuple[tuple[int, ...], float]:
    best_actions = None
    best_score = -1.0
    for actions in itertools.product(range(ACTIONS), repeat=horizon):
        distribution = [1.0 if state == start else 0.0 for state in range(SYMBOLS)]
        uncertainty = 0.0
        for action in actions:
            next_distribution = [0.0] * SYMBOLS
            for state, probability in enumerate(distribution):
                if probability == 0.0:
                    continue
                prediction = model.predict(state, action)
                for next_state, next_probability in enumerate(prediction):
                    next_distribution[next_state] += probability * next_probability
            distribution = next_distribution
            uncertainty += model.uncertainty(state, action)
        score = distribution[target] - uncertainty_penalty * (
            uncertainty / horizon
        )
        if score > best_score:
            best_score = score
            best_actions = actions
    assert best_actions is not None
    return best_actions, best_score


def _execute_plan(start: int, target: int, actions: tuple[int, ...]) -> bool:
    state = start
    for action in actions:
        state = _true_next(state, action)
    return state == target


def _planning_summary(
    model: _Ensemble,
    *,
    target: int = 3,
    horizon: int = 3,
) -> dict:
    summaries = {}
    for label, penalty in (("argmax", 0.0), ("uncertainty_penalized", 0.6)):
        successes = 0
        for state in TRAIN_STATES + OOD_STATES:
            actions, score = _plan(
                model,
                start=state,
                target=target,
                horizon=horizon,
                uncertainty_penalty=penalty,
            )
            successes += int(_execute_plan(state, target, actions))
        summaries[label] = {
            "episodes": len(TRAIN_STATES + OOD_STATES),
            "successes": successes,
            "success_rate": successes / len(TRAIN_STATES + OOD_STATES),
            "target": target,
            "horizon": horizon,
        }
    return summaries


def _sample_efficiency(
    *,
    seed: int,
    sizes: tuple[int, ...],
) -> dict:
    rows = _samples(
        seed=seed,
        states=TRAIN_STATES,
        samples_per_pair=max(sizes),
    )
    result = {}
    for size in sizes:
        limited = []
        for state in TRAIN_STATES:
            for action in range(ACTIONS):
                limited.extend(
                    [
                        row
                        for row in rows
                        if row[0] == state and row[1] == action
                    ][:size]
                )
        model = _split_models(limited)
        id_rows = [(state, action) for state in TRAIN_STATES for action in range(ACTIONS)]
        ood_rows = [(state, action) for state in OOD_STATES for action in range(ACTIONS)]
        result[size] = {
            "training_examples": len(limited),
            "id_accuracy": _stats(id_rows, model)["accuracy"],
            "ood_mean_uncertainty": _stats(ood_rows, model)["mean_uncertainty"],
        }
    return result


def run_world_model_calibration_probe(
    *,
    seed: int = 20261028,
    samples_per_pair: int = 20,
) -> dict:
    if samples_per_pair < 1:
        raise ValueError("samples_per_pair must be positive")
    train_rows = _samples(
        seed=seed,
        states=TRAIN_STATES,
        samples_per_pair=samples_per_pair,
    )
    model = _split_models(train_rows)
    id_rows = [(state, action) for state in TRAIN_STATES for action in range(ACTIONS)]
    ood_rows = [(state, action) for state in OOD_STATES for action in range(ACTIONS)]
    id_stats = _stats(id_rows, model)
    ood_stats = _stats(ood_rows, model)
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "model": {
            "kind": "two-table-model ensemble",
            "uncertainty": "normalized entropy plus ensemble disagreement",
        },
        "config": {
            "seed": seed,
            "samples_per_pair": samples_per_pair,
            "train_states": list(TRAIN_STATES),
            "ood_states": list(OOD_STATES),
            "symbols": SYMBOLS,
            "actions": ACTIONS,
        },
        "data": {
            "train_pairs": len(id_rows),
            "id_pairs": len(id_rows),
            "ood_pairs": len(ood_rows),
            "train_samples": len(train_rows),
        },
        "metrics": {
            "id_accuracy": id_stats["accuracy"],
            "ood_accuracy": ood_stats["accuracy"],
            "id_brier": id_stats["brier"],
            "ood_brier": ood_stats["brier"],
            "id_ece": id_stats["ece"],
            "ood_ece": ood_stats["ece"],
            "id_mean_uncertainty": id_stats["mean_uncertainty"],
            "ood_mean_uncertainty": ood_stats["mean_uncertainty"],
            "ood_error_auroc": ood_stats["uncertainty_error_auroc"],
            "counterfactual_error_id": _counterfactual_error(model, TRAIN_STATES),
            "counterfactual_error_ood": _counterfactual_error(model, OOD_STATES),
            "rollout_drift_id": _rollout_error(model, start=TRAIN_STATES[0]),
            "rollout_drift_ood": _rollout_error(model, start=OOD_STATES[0]),
        },
        "planning": _planning_summary(model),
        "sample_efficiency": _sample_efficiency(
            seed=seed,
            sizes=(1, 2, 5, samples_per_pair),
        ),
        "notes": [
            "OOD states are unseen in training and use the same symbolic transition rule.",
            "The probe measures calibration and planning on a synthetic table world, not pixels or a neural model.",
            "Uncertainty is not claimed to improve planning unless the planning field shows it.",
        ],
    }
