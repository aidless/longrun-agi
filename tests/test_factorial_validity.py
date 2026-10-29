import itertools
import random

import pytest

from longrun.analysis.factorial import (
    DesignError,
    benjamini_hochberg,
    estimate_factorial,
    holm_bonferroni,
    run_estimator_grid,
)


def _term_name(term):
    return "_x_".join(term)


def _mean_for_effects(level, factor_names, effects, intercept=0.5):
    value = intercept
    for size in range(1, len(factor_names) + 1):
        for term in itertools.combinations(factor_names, size):
            sign = 1
            for factor in term:
                index = factor_names.index(factor)
                sign *= 1 if level[index] == 0 else -1
            value += effects.get(_term_name(term), 0.0) * sign / 2
    return value


def _balanced_rows(
    *,
    factor_names=("A", "B"),
    effects=None,
    families=("f1", "f2"),
    episodes_per_cell=2,
    intercept=0.5,
):
    effects = effects or {}
    rows = []
    for family_id in families:
        for level in itertools.product((0, 1), repeat=len(factor_names)):
            outcome = _mean_for_effects(
                level, factor_names, effects, intercept=intercept
            )
            for episode in range(episodes_per_cell):
                rows.append(
                    {
                        "task_id": (
                            f"{family_id}-{''.join(map(str, level))}-{episode}"
                        ),
                        "family_id": family_id,
                        "factors": dict(zip(factor_names, level)),
                        "success": outcome,
                    }
                )
    return rows


def test_estimator_recovers_exact_two_factor_contrasts():
    effects = {"A": 0.20, "B": -0.10, "A_x_B": 0.30}
    result = estimate_factorial(
        _balanced_rows(effects=effects),
        ("A", "B"),
        bootstrap_replicates=100,
        seed=11,
    )

    for name, expected in effects.items():
        assert result["effects"][name]["estimate"] == pytest.approx(
            expected, abs=1e-12
        )
        assert result["effects"][name]["ci_low"] == pytest.approx(
            expected, abs=1e-12
        )
        assert result["effects"][name]["ci_high"] == pytest.approx(
            expected, abs=1e-12
        )
    assert result["bootstrap"]["method"] == "nested-family-episode"


def test_estimator_recovers_exact_three_factor_contrasts():
    factors = ("A", "B", "C")
    effects = {
        "A": 0.24,
        "B": -0.12,
        "C": 0.08,
        "A_x_B": 0.16,
        "A_x_C": -0.04,
        "B_x_C": 0.06,
        "A_x_B_x_C": 0.10,
    }
    result = estimate_factorial(
        _balanced_rows(factor_names=factors, effects=effects),
        factors,
        bootstrap_replicates=100,
        seed=12,
    )

    for name, expected in effects.items():
        assert result["effects"][name]["estimate"] == pytest.approx(
            expected, abs=1e-12
        )


@pytest.mark.parametrize(
    "factor_names, expected",
    [
        (("A", "A"), "duplicate"),
        (("A",), "at least two"),
        (("A", ""), "non-empty"),
        (("A", "B", "B"), "duplicate"),
    ],
)
def test_estimator_rejects_invalid_factor_names(factor_names, expected):
    with pytest.raises(DesignError, match=expected):
        estimate_factorial(
            _balanced_rows(), factor_names, bootstrap_replicates=10, seed=1
        )


@pytest.mark.parametrize(
    "mutation, expected",
    [
        (lambda row: row["factors"].update(C=0), "unknown factor"),
        (lambda row: row["factors"].pop("B"), "missing factor"),
        (lambda row: row["factors"].update(A=True), "integer 0 or 1"),
        (lambda row: row["factors"].update(A=1.0), "integer 0 or 1"),
        (lambda row: row["factors"].update(A=2), "integer 0 or 1"),
        (lambda row: row.pop("success"), "missing field"),
        (lambda row: row.update(success=float("nan")), "finite"),
    ],
)
def test_estimator_rejects_malformed_rows(mutation, expected):
    rows = _balanced_rows()
    mutation(rows[0])
    with pytest.raises(DesignError, match=expected):
        estimate_factorial(rows, ("A", "B"), bootstrap_replicates=10, seed=1)


def test_estimator_rejects_duplicate_episode_ids():
    rows = _balanced_rows()
    rows[1]["task_id"] = rows[0]["task_id"]
    with pytest.raises(DesignError, match="duplicate episode"):
        estimate_factorial(rows, ("A", "B"), bootstrap_replicates=10, seed=1)


def test_estimator_rejects_missing_and_unbalanced_cells():
    missing = [
        row
        for row in _balanced_rows()
        if row["factors"] != {"A": 1, "B": 1}
    ]
    with pytest.raises(DesignError, match="missing factorial cell"):
        estimate_factorial(missing, ("A", "B"), bootstrap_replicates=10, seed=1)

    unbalanced = _balanced_rows()
    extra = dict(unbalanced[0])
    extra["task_id"] = "extra"
    unbalanced.append(extra)
    with pytest.raises(DesignError, match="unbalanced cell"):
        estimate_factorial(
            unbalanced, ("A", "B"), bootstrap_replicates=10, seed=1
        )


def test_estimator_rejects_a_family_without_a_cell():
    rows = [
        row
        for row in _balanced_rows()
        if not (
            row["family_id"] == "f1"
            and row["factors"] == {"A": 1, "B": 1}
        )
    ]
    with pytest.raises(DesignError, match="family.*missing factorial cell"):
        estimate_factorial(rows, ("A", "B"), bootstrap_replicates=10, seed=1)


def test_estimator_is_invariant_to_row_order_and_fixed_seed():
    rows = _balanced_rows(effects={"A": 0.2, "A_x_B": 0.1})
    first = estimate_factorial(
        rows, ("A", "B"), bootstrap_replicates=80, seed=99
    )
    shuffled = list(rows)
    random.Random(7).shuffle(shuffled)
    second = estimate_factorial(
        shuffled, ("A", "B"), bootstrap_replicates=80, seed=99
    )
    assert first == second


def test_holm_and_bh_adjustments_are_monotone():
    p_values = {"A": 0.01, "B": 0.06, "A_x_B": 0.03}
    holm = holm_bonferroni(p_values, alpha=0.05)
    bh = benjamini_hochberg(p_values, alpha=0.05)

    assert holm["A"]["reject"] is True
    assert holm["A_x_B"]["p_adjusted"] == pytest.approx(0.06)
    assert holm["A_x_B"]["reject"] is False
    assert holm["B"]["p_adjusted"] == pytest.approx(0.06)
    assert bh["A"]["reject"] is True
    assert bh["A_x_B"]["reject"] is True
    assert bh["B"]["reject"] is False


def test_monte_carlo_grid_reports_required_validity_metrics():
    grid = run_estimator_grid(
        repetitions=2,
        bootstrap_replicates=20,
        base_seed=1234,
    )
    assert grid["repetitions"] == 2
    assert grid["bootstrap_replicates"] == 20
    assert grid["metrics"]["cell_balance"]["null"]["balanced"] is True
    assert (
        grid["metrics"]["cell_balance"]["alternative"]["balanced"] is True
    )
    for key in ("bias", "rmse", "ci_coverage"):
        assert key in grid["metrics"]["estimation"]
    assert grid["metrics"]["multiplicity"]["null"]["fwer"] >= 0.0
    assert grid["metrics"]["multiplicity"]["null"]["fwer_method"] == (
        "holm-bonferroni"
    )
    assert grid["metrics"]["multiplicity"]["alternative"][
        "power_any_true_effect"
    ] >= 0.0
    assert grid["metrics"]["multiplicity"]["alternative"]["fdr_method"] == (
        "benjamini-hochberg"
    )
    alternative_effects = grid["config"]["alternative_effects"]
    true_terms = {
        term for term, value in alternative_effects.items() if value != 0.0
    }
    null_terms = set(alternative_effects) - true_terms
    assert true_terms
    assert null_terms
    assert set(
        grid["metrics"]["multiplicity"]["alternative"]["null_terms"]
    ) == null_terms
    assert all(
        0.0 < probability < 1.0
        for probability in grid["config"]["planted_cell_probabilities"].values()
    )
