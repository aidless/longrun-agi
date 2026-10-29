"""CPU-only research probes for the LongRun-AGI program."""

from .compute import run_compute_probe
from .goal_drift import run_goal_drift_probe
from .verifier_gap import run_verifier_gap_probe
from .world_model import run_world_model_probe

__all__ = [
    "run_compute_probe",
    "run_goal_drift_probe",
    "run_verifier_gap_probe",
    "run_world_model_probe",
]
