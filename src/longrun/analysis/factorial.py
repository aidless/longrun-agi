from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from statistics import fmean


class DesignError(ValueError):
    """Raised when rows do not form a supported balanced factorial design."""


@dataclass(frozen=True, slots=True)
class _Row:
    task_id: str
    family_id: str
    levels: tuple[int, ...]
    success: float


_TERM_SEPARATOR = "_x_"
_REQUIRED_ROW_FIELDS = ("task_id", "family_id", "factors", "success")


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _validate_config(
    factor_names: Sequence[str],
    bootstrap_replicates: int,
    confidence_level: float,
    alpha: float,
    seed: int,
) -> tuple[str, ...]:
    if isinstance(factor_names, (str, bytes)) or not isinstance(
        factor_names, Sequence
    ):
        raise DesignError("factor_names must be a sequence of strings")
    names = tuple(factor_names)
    if len(names) < 2:
        raise DesignError("at least two factors are required")
    if any(not isinstance(name, str) or not name.strip() for name in names):
        raise DesignError("factor names must be non-empty strings")
    if len(set(names)) != len(names):
        raise DesignError("duplicate factor names are not allowed")
    if _TERM_SEPARATOR in "".join(names):
        raise DesignError(
            f"factor names cannot contain the reserved separator {_TERM_SEPARATOR!r}"
        )
    if isinstance(bootstrap_replicates, bool) or not isinstance(
        bootstrap_replicates, int
    ):
        raise DesignError("bootstrap_replicates must be an integer")
    if bootstrap_replicates < 1:
        raise DesignError("bootstrap_replicates must be positive")
    if not 0.0 < confidence_level < 1.0:
        raise DesignError("confidence_level must be between 0 and 1")
    if not 0.0 < alpha < 1.0:
        raise DesignError("alpha must be between 0 and 1")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise DesignError("seed must be an integer")
    return names


def _normalize_rows(
    rows: Iterable[Mapping[str, object]], factor_names: tuple[str, ...]
) -> list[_Row]:
    normalized: list[_Row] = []
    seen_task_ids: set[str] = set()
    expected_factors = set(factor_names)
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise DesignError(f"row {index} must be a mapping")
        missing_fields = [name for name in _REQUIRED_ROW_FIELDS if name not in raw]
        if missing_fields:
            raise DesignError(
                f"row {index} is missing field(s): {', '.join(missing_fields)}"
            )

        task_id = raw["task_id"]
        family_id = raw["family_id"]
        if not isinstance(task_id, str) or not task_id:
            raise DesignError(f"row {index} task_id must be a non-empty string")
        if not isinstance(family_id, str) or not family_id:
            raise DesignError(f"row {index} family_id must be a non-empty string")
        if task_id in seen_task_ids:
            raise DesignError(f"duplicate episode task_id: {task_id!r}")
        seen_task_ids.add(task_id)

        factors = raw["factors"]
        if not isinstance(factors, Mapping):
            raise DesignError(f"row {task_id!r} factors must be a mapping")
        factor_keys = set(factors)
        unknown = factor_keys - expected_factors
        if unknown:
            raise DesignError(
                f"row {task_id!r} has unknown factor(s): "
                f"{', '.join(sorted(map(str, unknown)))}"
            )
        missing = expected_factors - factor_keys
        if missing:
            raise DesignError(
                f"row {task_id!r} is missing factor(s): "
                f"{', '.join(sorted(missing))}"
            )

        levels: list[int] = []
        for name in factor_names:
            value = factors[name]
            if isinstance(value, bool) or not isinstance(value, int) or value not in {
                0,
                1,
            }:
                raise DesignError(
                    f"row {task_id!r} factor {name!r} must be integer 0 or 1"
                )
            levels.append(value)

        success = raw["success"]
        if (
            isinstance(success, bool)
            or not isinstance(success, (int, float))
            or not math.isfinite(float(success))
            or not 0.0 <= float(success) <= 1.0
        ):
            raise DesignError(
                f"row {task_id!r} success must be a finite number in [0, 1]"
            )
        normalized.append(
            _Row(
                task_id=task_id,
                family_id=family_id,
                levels=tuple(levels),
                success=float(success),
            )
        )

    if not normalized:
        raise DesignError("at least one episode row is required")
    return sorted(
        normalized,
        key=lambda row: (row.family_id, row.levels, row.task_id),
    )


def _all_cells(factor_count: int) -> list[tuple[int, ...]]:
    return list(itertools.product((0, 1), repeat=factor_count))


def _term_name(term: tuple[str, ...]) -> str:
    return _TERM_SEPARATOR.join(term)


def _terms(factor_names: tuple[str, ...]) -> list[tuple[str, ...]]:
    return [
        term
        for size in range(1, len(factor_names) + 1)
        for term in itertools.combinations(factor_names, size)
    ]


def _group_rows(
    rows: list[_Row], factor_names: tuple[str, ...]
) -> dict[str, dict[tuple[int, ...], list[float]]]:
    grouped: dict[str, dict[tuple[int, ...], list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        grouped[row.family_id][row.levels].append(row.success)
    return {
        family_id: {
            levels: values
            for levels, values in sorted(cells.items())
        }
        for family_id, cells in sorted(grouped.items())
    }


def _check_balance(
    grouped: Mapping[str, Mapping[tuple[int, ...], Sequence[float]]],
    factor_names: tuple[str, ...],
) -> dict:
    expected_cells = _all_cells(len(factor_names))
    family_count = len(grouped)
    if family_count < 2:
        raise DesignError(
            "at least two families are required for cluster inference"
        )

    for family_id, cells in grouped.items():
        missing = [cell for cell in expected_cells if cell not in cells]
        if missing:
            raise DesignError(
                f"family {family_id!r} is missing factorial cell(s): {missing!r}"
            )
        counts = {cell: len(cells[cell]) for cell in expected_cells}
        if len(set(counts.values())) != 1:
            raise DesignError(
                f"family {family_id!r} has an unbalanced cell: {counts!r}"
            )
        if next(iter(counts.values())) < 1:
            raise DesignError(f"family {family_id!r} has an empty factorial cell")

    all_counts = {
        cell: sum(len(cells[cell]) for cells in grouped.values())
        for cell in expected_cells
    }
    if len(set(all_counts.values())) != 1:
        raise DesignError(f"design has an unbalanced cell: {all_counts!r}")

    episodes_per_cell = next(iter(all_counts.values()))
    return {
        "balanced": True,
        "families": family_count,
        "cells": len(expected_cells),
        "episodes_per_family_cell": episodes_per_cell,
        "episodes_per_cell": episodes_per_cell * family_count,
        "total_episodes": len(expected_cells) * episodes_per_cell * family_count,
        "cell_counts": {
            "".join(map(str, cell)): all_counts[cell]
            for cell in expected_cells
        },
    }


def _cell_signs(
    factor_names: tuple[str, ...], term: tuple[str, ...], cell: tuple[int, ...]
) -> int:
    sign = 1
    for factor in term:
        index = factor_names.index(factor)
        sign *= 1 if cell[index] == 0 else -1
    return sign


def _contrasts(
    cell_means: Mapping[tuple[int, ...], float],
    factor_names: tuple[str, ...],
) -> dict[str, float]:
    expected_cells = _all_cells(len(factor_names))
    divisor = 2 ** (len(factor_names) - 1)
    return {
        _term_name(term): sum(
            _cell_signs(factor_names, term, cell) * cell_means[cell]
            for cell in expected_cells
        )
        / divisor
        for term in _terms(factor_names)
    }


def _equal_weight_cell_means(
    grouped: Mapping[str, Mapping[tuple[int, ...], Sequence[float]]],
    factor_names: tuple[str, ...],
) -> dict[tuple[int, ...], float]:
    expected_cells = _all_cells(len(factor_names))
    family_means = {
        cell: [
            fmean(grouped[family_id][cell])
            for family_id in sorted(grouped)
        ]
        for cell in expected_cells
    }
    return {
        cell: fmean(values)
        for cell, values in family_means.items()
    }


def _quantile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("cannot take a quantile of an empty sequence")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    fraction = position - lower
    return (
        sorted_values[lower] * (1.0 - fraction)
        + sorted_values[upper] * fraction
    )


def _bootstrap_effects(
    grouped: Mapping[str, Mapping[tuple[int, ...], Sequence[float]]],
    factor_names: tuple[str, ...],
    *,
    replicates: int,
    rng: random.Random,
) -> dict[str, list[float]]:
    expected_cells = _all_cells(len(factor_names))
    family_ids = sorted(grouped)
    term_names = [_term_name(term) for term in _terms(factor_names)]
    draws: dict[str, list[float]] = {name: [] for name in term_names}

    for _ in range(replicates):
        sampled_families = [
            family_ids[rng.randrange(len(family_ids))]
            for _ in family_ids
        ]
        cell_means: dict[tuple[int, ...], float] = {}
        for cell in expected_cells:
            values: list[float] = []
            for family_id in sampled_families:
                family_values = grouped[family_id][cell]
                values.extend(
                    family_values[rng.randrange(len(family_values))]
                    for _ in family_values
                )
            cell_means[cell] = fmean(values)
        contrasts = _contrasts(cell_means, factor_names)
        for name in term_names:
            draws[name].append(contrasts[name])
    return draws


def _bootstrap_p_value(estimate: float, draws: Sequence[float]) -> float:
    if estimate == 0.0:
        return 1.0
    tolerance = abs(estimate)
    centered = [draw - estimate for draw in draws]
    lower = sum(value <= -tolerance for value in centered)
    upper = sum(value >= tolerance for value in centered)
    return min(1.0, 2.0 * (1 + min(lower, upper)) / (len(draws) + 1))


def _validate_probability_mapping(p_values: Mapping[str, float]) -> dict[str, float]:
    if not p_values:
        raise DesignError("at least one p-value is required")
    validated: dict[str, float] = {}
    for name, value in p_values.items():
        if not isinstance(name, str) or not name:
            raise DesignError("p-value names must be non-empty strings")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or not 0.0 <= float(value) <= 1.0
        ):
            raise DesignError(f"p-value for {name!r} must be in [0, 1]")
        validated[name] = float(value)
    return validated


def holm_bonferroni(
    p_values: Mapping[str, float], *, alpha: float = 0.05
) -> dict[str, dict]:
    """Holm step-down adjustment for strong family-wise error control."""
    if not 0.0 < alpha < 1.0:
        raise DesignError("alpha must be between 0 and 1")
    validated = _validate_probability_mapping(p_values)
    ordered = sorted(validated.items(), key=lambda item: (item[1], item[0]))
    total = len(ordered)
    adjusted: dict[str, dict] = {}
    running = 0.0
    for rank, (name, p_value) in enumerate(ordered, start=1):
        running = max(running, min(1.0, p_value * (total - rank + 1)))
        adjusted[name] = {
            "p_value": p_value,
            "p_adjusted": running,
            "rank": rank,
            "reject": running <= alpha,
        }
    return {
        name: adjusted[name]
        for name in validated
    }


def benjamini_hochberg(
    p_values: Mapping[str, float], *, alpha: float = 0.05
) -> dict[str, dict]:
    """Benjamini-Hochberg step-up adjustment for false discovery rate."""
    if not 0.0 < alpha < 1.0:
        raise DesignError("alpha must be between 0 and 1")
    validated = _validate_probability_mapping(p_values)
    ordered = sorted(validated.items(), key=lambda item: (item[1], item[0]))
    total = len(ordered)
    adjusted_values: list[float] = []
    running = 1.0
    for rank in range(total, 0, -1):
        name, p_value = ordered[rank - 1]
        running = min(running, min(1.0, p_value * total / rank))
        adjusted_values.append(running)
    adjusted_values.reverse()
    return {
        name: {
            "p_value": p_value,
            "p_adjusted": adjusted_values[rank - 1],
            "rank": rank,
            "reject": adjusted_values[rank - 1] <= alpha,
        }
        for rank, (name, p_value) in enumerate(ordered, start=1)
    }


def estimate_factorial(
    rows: Iterable[Mapping[str, object]],
    factor_names: Sequence[str],
    *,
    bootstrap_replicates: int = 999,
    confidence_level: float = 0.95,
    alpha: float = 0.05,
    seed: int = 0,
) -> dict:
    """Estimate orthogonal contrasts with nested family/episode bootstrap CIs."""
    names = _validate_config(
        factor_names,
        bootstrap_replicates,
        confidence_level,
        alpha,
        seed,
    )
    normalized = _normalize_rows(rows, names)
    grouped = _group_rows(normalized, names)
    balance = _check_balance(grouped, names)
    cell_means = _equal_weight_cell_means(grouped, names)
    estimates = _contrasts(cell_means, names)

    rng = random.Random(seed)
    draws = _bootstrap_effects(
        grouped,
        names,
        replicates=bootstrap_replicates,
        rng=rng,
    )
    tail = (1.0 - confidence_level) / 2.0
    effects: dict[str, dict] = {}
    for term in _terms(names):
        name = _term_name(term)
        values = draws[name]
        ordered = sorted(values)
        estimate = estimates[name]
        if len(values) > 1:
            mean = fmean(values)
            variance = sum((value - mean) ** 2 for value in values) / (
                len(values) - 1
            )
            standard_error = math.sqrt(variance)
        else:
            standard_error = 0.0
        effects[name] = {
            "estimate": estimate,
            "ci_low": _quantile(ordered, tail),
            "ci_high": _quantile(ordered, 1.0 - tail),
            "bootstrap_se": standard_error,
            "p_value": _bootstrap_p_value(estimate, values),
        }

    p_values = {
        name: row["p_value"] for name, row in effects.items()
    }
    holm = holm_bonferroni(p_values, alpha=alpha)
    bh = benjamini_hochberg(p_values, alpha=alpha)
    for name in effects:
        effects[name].update(
            {
                "p_holm": holm[name]["p_adjusted"],
                "reject_holm": holm[name]["reject"],
                "p_bh": bh[name]["p_adjusted"],
                "reject_bh": bh[name]["reject"],
            }
        )

    normalized_payload = [
        {
            "task_id": row.task_id,
            "family_id": row.family_id,
            "factors": dict(zip(names, row.levels)),
            "success": row.success,
        }
        for row in normalized
    ]
    input_digest = hashlib.sha256(
        _canonical_json(
            {
                "factor_names": names,
                "rows": normalized_payload,
            }
        ).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": 1,
        "status": "harness-validation",
        "scientific_result": False,
        "factors": list(names),
        "design": {
            **balance,
            "input_sha256": input_digest,
            "weighting": "family and cell equal weight",
            "contrast_scale": "level 0 minus level 1; unnormalized interactions",
        },
        "bootstrap": {
            "method": "nested-family-episode",
            "replicates": bootstrap_replicates,
            "confidence_level": confidence_level,
            "seed": seed,
            "interval": "percentile",
            "p_value": "two-sided bootstrap null centered at the estimate",
        },
        "effects": effects,
        "multiplicity": {
            "alpha": alpha,
            "fwer_method": "holm-bonferroni",
            "fdr_method": "benjamini-hochberg",
            "holm": holm,
            "benjamini_hochberg": bh,
        },
    }


def _true_cell_probability(
    levels: tuple[int, ...],
    factor_names: tuple[str, ...],
    effects: Mapping[str, float],
    intercept: float,
) -> float:
    value = intercept
    for term in _terms(factor_names):
        value += (
            effects.get(_term_name(term), 0.0)
            * _cell_signs(factor_names, term, levels)
            / 2.0
        )
    return value


def _simulate_rows(
    factor_names: tuple[str, ...],
    effects: Mapping[str, float],
    *,
    families: int,
    episodes_per_cell: int,
    intercept: float,
    family_noise: float,
    rng: random.Random,
    label: str,
    repetition: int,
) -> list[dict]:
    rows: list[dict] = []
    cells = _all_cells(len(factor_names))
    for family_index in range(families):
        family_id = f"family-{family_index:02d}"
        offset = rng.uniform(-family_noise, family_noise)
        for cell in cells:
            probability = _true_cell_probability(
                cell,
                factor_names,
                effects,
                intercept,
            )
            probability = min(0.95, max(0.05, probability + offset))
            for episode in range(episodes_per_cell):
                rows.append(
                    {
                        "task_id": (
                            f"{label}-r{repetition:04d}-{family_id}-"
                            f"{''.join(map(str, cell))}-e{episode:02d}"
                        ),
                        "family_id": family_id,
                        "factors": dict(zip(factor_names, cell)),
                        "success": float(rng.random() < probability),
                    }
                )
    return rows


def _simulation_balance(
    rows: Sequence[Mapping[str, object]],
    factor_names: tuple[str, ...],
) -> dict:
    counts: dict[tuple[str, tuple[int, ...]], int] = defaultdict(int)
    for row in rows:
        levels = tuple(
            int(row["factors"][name]) for name in factor_names
        )
        counts[(str(row["family_id"]), levels)] += 1
    expected = _all_cells(len(factor_names))
    families = sorted({str(row["family_id"]) for row in rows})
    per_cell = {
        "".join(map(str, cell)): sum(
            counts[(family, cell)] for family in families
        )
        for cell in expected
    }
    family_cell_counts = {
        counts[(family, cell)]
        for family in families
        for cell in expected
    }
    return {
        "balanced": len(family_cell_counts) == 1,
        "families": len(families),
        "cells": len(expected),
        "episodes_per_cell": (
            next(iter(family_cell_counts)) * len(families)
            if len(family_cell_counts) == 1
            else None
        ),
        "cell_counts": per_cell,
        "total_episodes": len(rows),
    }


def _metric_summary(
    repetitions: Sequence[dict],
    planted: Mapping[str, float],
    term_names: Sequence[str],
) -> dict:
    estimates = {
        term: [row["effects"][term]["estimate"] for row in repetitions]
        for term in term_names
    }
    coverage = {
        term: fmean(
            float(
                row["effects"][term]["ci_low"]
                <= planted[term]
                <= row["effects"][term]["ci_high"]
            )
            for row in repetitions
        )
        for term in term_names
    }
    widths = {
        term: fmean(
            row["effects"][term]["ci_high"]
            - row["effects"][term]["ci_low"]
            for row in repetitions
        )
        for term in term_names
    }
    truth = {term: float(planted[term]) for term in term_names}
    bias = {
        term: fmean(estimates[term]) - truth[term] for term in term_names
    }
    rmse = {
        term: math.sqrt(
            fmean(
                (estimate - truth[term]) ** 2
                for estimate in estimates[term]
            )
        )
        for term in term_names
    }
    return {
        "recovery": {
            term: fmean(values) for term, values in estimates.items()
        },
        "bias": bias,
        "rmse": rmse,
        "ci_coverage": coverage,
        "overall_ci_coverage": fmean(coverage.values()),
        "mean_ci_width": widths,
        "overall_mean_ci_width": fmean(widths.values()),
    }


def _null_multiplicity(
    repetitions: Sequence[dict],
    term_names: Sequence[str],
) -> dict:
    rejections = {
        term: fmean(
            float(row["effects"][term]["reject_holm"])
            for row in repetitions
        )
        for term in term_names
    }
    return {
        "repetitions": len(repetitions),
        "fwer_method": "holm-bonferroni",
        "fwer": fmean(
            float(
                any(
                    row["effects"][term]["reject_holm"]
                    for term in term_names
                )
            )
            for row in repetitions
        ),
        "per_term_false_rejection_rate": rejections,
        "mean_rejections": fmean(
            sum(
                row["effects"][term]["reject_holm"]
                for term in term_names
            )
            for row in repetitions
        ),
    }


def _alternative_multiplicity(
    repetitions: Sequence[dict],
    planted: Mapping[str, float],
    term_names: Sequence[str],
) -> dict:
    true_terms = [term for term in term_names if planted[term] != 0.0]
    false_terms = [term for term in term_names if planted[term] == 0.0]
    term_power = {
        term: fmean(
            float(row["effects"][term]["reject_holm"])
            for row in repetitions
        )
        for term in true_terms
    }
    false_discovery_proportions = []
    mean_discoveries = []
    mean_false_discoveries = []
    for row in repetitions:
        discoveries = sum(
            row["effects"][term]["reject_bh"] for term in term_names
        )
        false_discoveries = sum(
            row["effects"][term]["reject_bh"] for term in false_terms
        )
        mean_discoveries.append(discoveries)
        mean_false_discoveries.append(false_discoveries)
        false_discovery_proportions.append(
            false_discoveries / max(1, discoveries)
        )
    total_discoveries = sum(mean_discoveries)
    total_false = sum(mean_false_discoveries)
    return {
        "repetitions": len(repetitions),
        "fdr_method": "benjamini-hochberg",
        "true_positive_terms": true_terms,
        "null_terms": false_terms,
        "power_any_true_effect": fmean(
            float(
                any(
                    row["effects"][term]["reject_holm"]
                    for term in true_terms
                )
            )
            for row in repetitions
        ),
        "power_by_term": term_power,
        "fdr": fmean(false_discovery_proportions),
        "pooled_false_discovery_fraction": (
            total_false / total_discoveries if total_discoveries else 0.0
        ),
        "false_discoveries": total_false,
        "discoveries": total_discoveries,
        "mean_discoveries": fmean(mean_discoveries),
        "mean_false_discoveries": fmean(mean_false_discoveries),
    }


def run_estimator_grid(
    *,
    repetitions: int = 200,
    bootstrap_replicates: int = 299,
    base_seed: int = 20261027,
    confidence_level: float = 0.95,
    alpha: float = 0.05,
) -> dict:
    """Run a fixed-seed CPU Monte Carlo grid for estimator validity."""
    if isinstance(repetitions, bool) or not isinstance(repetitions, int):
        raise DesignError("repetitions must be an integer")
    if repetitions < 1:
        raise DesignError("repetitions must be positive")
    if isinstance(base_seed, bool) or not isinstance(base_seed, int):
        raise DesignError("base_seed must be an integer")

    factor_names = ("A", "B", "C")
    term_names = [_term_name(term) for term in _terms(factor_names)]
    null_effects = {term: 0.0 for term in term_names}
    alternative_effects = {
        "A": 0.25,
        "B": -0.20,
        "C": 0.15,
        "A_x_B": 0.10,
        "A_x_C": 0.0,
        "B_x_C": 0.0,
        "A_x_B_x_C": 0.08,
    }
    config = {
        "factors": list(factor_names),
        "families": 24,
        "episodes_per_family_cell": 20,
        "intercept": 0.50,
        "family_noise_half_width": 0.02,
        "outcome": "Bernoulli(success probability)",
        "null_effects": null_effects,
        "alternative_effects": alternative_effects,
        "planted_cell_probabilities": {
            "".join(map(str, cell)): _true_cell_probability(
                cell,
                factor_names,
                alternative_effects,
                intercept=0.50,
            )
            for cell in _all_cells(len(factor_names))
        },
        "planting_status": "probability-clipping-disabled",
    }
    rng = random.Random(base_seed)
    null_runs: list[dict] = []
    alternative_runs: list[dict] = []
    null_balances: list[dict] = []
    alternative_balances: list[dict] = []

    for repetition in range(repetitions):
        rows = _simulate_rows(
            factor_names,
            null_effects,
            families=config["families"],
            episodes_per_cell=config["episodes_per_family_cell"],
            intercept=config["intercept"],
            family_noise=config["family_noise_half_width"],
            rng=rng,
            label="null",
            repetition=repetition,
        )
        null_balances.append(_simulation_balance(rows, factor_names))
        null_runs.append(
            estimate_factorial(
                rows,
                factor_names,
                bootstrap_replicates=bootstrap_replicates,
                confidence_level=confidence_level,
                alpha=alpha,
                seed=rng.randrange(2**32),
            )
        )

        rows = _simulate_rows(
            factor_names,
            alternative_effects,
            families=config["families"],
            episodes_per_cell=config["episodes_per_family_cell"],
            intercept=config["intercept"],
            family_noise=config["family_noise_half_width"],
            rng=rng,
            label="alternative",
            repetition=repetition,
        )
        alternative_balances.append(_simulation_balance(rows, factor_names))
        alternative_runs.append(
            estimate_factorial(
                rows,
                factor_names,
                bootstrap_replicates=bootstrap_replicates,
                confidence_level=confidence_level,
                alpha=alpha,
                seed=rng.randrange(2**32),
            )
        )

    estimation = _metric_summary(
        alternative_runs,
        alternative_effects,
        term_names,
    )
    null_diagnostics = _metric_summary(
        null_runs,
        null_effects,
        term_names,
    )
    multiplicity = {
        "null": _null_multiplicity(null_runs, term_names),
        "alternative": _alternative_multiplicity(
            alternative_runs,
            alternative_effects,
            term_names,
        ),
    }
    return {
        "schema_version": 1,
        "status": "harness-validation",
        "scientific_result": False,
        "seed": base_seed,
        "repetitions": repetitions,
        "bootstrap_replicates": bootstrap_replicates,
        "confidence_level": confidence_level,
        "alpha": alpha,
        "config": config,
        "metrics": {
            "cell_balance": {
                "null": {
                    "balanced": all(
                        balance["balanced"] for balance in null_balances
                    ),
                    "example": null_balances[0],
                },
                "alternative": {
                    "balanced": all(
                        balance["balanced"]
                        for balance in alternative_balances
                    ),
                    "example": alternative_balances[0],
                },
            },
            "estimation": estimation,
            "null_diagnostics": null_diagnostics,
            "multiplicity": multiplicity,
        },
        "checks": {
            "all_runs_completed": (
                len(null_runs) == repetitions
                and len(alternative_runs) == repetitions
            ),
            "design_balanced": (
                all(balance["balanced"] for balance in null_balances)
                and all(
                    balance["balanced"]
                    for balance in alternative_balances
                )
            ),
            "scientific_thresholds_applied": False,
            "note": (
                "The grid validates estimator execution and reports finite-sample "
                "behavior; it does not by itself validate any agent or claim novelty."
            ),
        },
    }
