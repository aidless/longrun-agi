from __future__ import annotations

from dataclasses import replace

from .env import FileOpsEnv
from .generators import generate_tasks
from .models import Action, FaultSpec, Observation, Op
from .policies import PolicyError, _SpecPolicyBase


class _OneFaultEnv(FileOpsEnv):
    def __init__(self, task, fault_kind: str):
        super().__init__(task)
        self.fault_kind = fault_kind
        self._fault_used = False
        self.permanent_error = False

    def step(self, action: Action) -> Observation:
        if self.fault_kind == "schema_corruption" and action.op is Op.READ:
            if not self._fault_used:
                self._fault_used = True
                self.step_count += 1
                self.permanent_error = True
                return Observation(
                    False,
                    "schema_corruption: RULE_JSON is malformed",
                    step=self.step_count,
                    fault_kind="schema_corruption",
                )
        if self.fault_kind == "missing_source" and action.op is Op.READ:
            if not self._fault_used:
                self._fault_used = True
                self.step_count += 1
                self.permanent_error = True
                return Observation(
                    False,
                    "missing_source: docs/SPEC.md disappeared",
                    step=self.step_count,
                    fault_kind="missing_source",
                )
        return super().step(action)


class _RetryingPolicy(_SpecPolicyBase):
    name = "retrying"

    def __init__(self):
        super().__init__(retain_rule=False, retry_on_error=True)


class _NoRetryPolicy(_SpecPolicyBase):
    name = "no-retry"

    def __init__(self):
        super().__init__(retain_rule=False, retry_on_error=False)


def _run_fault(task, policy, fault_kind: str, fault_op: Op | None) -> dict:
    env = _OneFaultEnv(task, fault_kind)
    observation = Observation(ok=True, message="start", step=0, done=False)
    policy.reset()
    error = None
    for _ in range(task.max_steps + 3):
        if fault_op is not None and env.fault_kind not in {
            "schema_corruption",
            "missing_source",
        }:
            # Injected by the deterministic fault list in the task.
            pass
        try:
            observation = env.step(policy.act(observation))
        except (PolicyError, ValueError, KeyError) as exc:
            error = f"{type(exc).__name__}: {exc}"
            break
        if observation.done:
            break
    return {
        "fault_kind": fault_kind,
        "success": env.is_success() and error is None and not env.permanent_error,
        "steps": env.step_count,
        "faults_injected": list(env.faults_injected),
        "error": error or (None if env.is_success() else observation.message),
    }


def run_failure_matrix() -> dict:
    """Exercise one recoverable fault and two unrecoverable schema faults."""
    base = generate_tasks(instances_per_variant=1)[0]
    transient_specs = {
        "transient_read": (Op.READ, "transient_read"),
        "transient_list": (Op.LIST, "transient_list"),
        "transient_move": (Op.MOVE, "transient_move"),
    }
    rows = []
    for name, (op, kind) in transient_specs.items():
        task = replace(
            base,
            faults=(FaultSpec(op=op, occurrence=1, kind=kind),),
        )
        recovered = _run_fault(task, _RetryingPolicy(), name, op)
        aborted = _run_fault(task, _NoRetryPolicy(), name, op)
        rows.append(
            {
                "fault_kind": name,
                "retry_success": recovered["success"],
                "no_retry_success": aborted["success"],
                "retry_recovers": (
                    recovered["success"] and not aborted["success"]
                ),
            }
        )

    for kind in ("schema_corruption", "missing_source"):
        recovered = _run_fault(base, _RetryingPolicy(), kind, Op.READ)
        rows.append(
            {
                "fault_kind": kind,
                "retry_success": recovered["success"],
                "no_retry_success": recovered["success"],
                "retry_recovers": False,
            }
        )
    recoverable = sum(row["retry_recovers"] for row in rows)
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "rows": rows,
        "recoverable": recoverable,
        "fatal": len(rows) - recoverable,
        "notes": [
            "The schema and missing-source faults are permanent and must not be counted as retry recovery.",
            "This matrix tests a scripted policy, not a model.",
        ],
    }
