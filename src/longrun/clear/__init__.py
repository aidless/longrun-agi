"""CLEAR-Bench: paired rule-shift tasks for long-horizon agents."""

from .env import FileOpsEnv
from .generators import generate_factorial_tasks, generate_fault_tasks, generate_tasks
from .models import Action, FaultSpec, Observation, Op, Task
from .policies import (
    ConfigurableSpecPolicy,
    PolicyError,
    ReactiveSpecPolicy,
    StickySpecPolicy,
)
from .runner import evaluate, factorial_effects, run_episode

__all__ = [
    "Action",
    "ConfigurableSpecPolicy",
    "FaultSpec",
    "FileOpsEnv",
    "Observation",
    "Op",
    "PolicyError",
    "ReactiveSpecPolicy",
    "StickySpecPolicy",
    "Task",
    "evaluate",
    "factorial_effects",
    "generate_factorial_tasks",
    "generate_fault_tasks",
    "generate_tasks",
    "run_episode",
]
