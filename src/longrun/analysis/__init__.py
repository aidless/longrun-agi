"""Statistical validation utilities for the CPU-first research harness."""

from .factorial import (
    DesignError,
    benjamini_hochberg,
    estimate_factorial,
    holm_bonferroni,
    run_estimator_grid,
)

__all__ = [
    "DesignError",
    "benjamini_hochberg",
    "estimate_factorial",
    "holm_bonferroni",
    "run_estimator_grid",
]
