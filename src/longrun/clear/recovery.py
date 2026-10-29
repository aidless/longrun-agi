from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import fmean


class FaultKind(str, Enum):
    STALE_STATE = "stale_state"
    TOOL_ERROR = "tool_error"
    MISLEADING_DOC = "misleading_doc"
    RULE_CHANGE = "rule_change"


class RecoveryAction(str, Enum):
    READ = "read"
    ACT = "act"
    VALIDATE = "validate"
    ROLLBACK = "rollback"
    REPLAN = "replan"
    HELP = "help"
    FINISH = "finish"


@dataclass(frozen=True, slots=True)
class RecoveryTask:
    task_id: str
    fault_kind: FaultKind
    initial_rule: str
    corrected_rule: str
    max_steps: int = 12


@dataclass(frozen=True, slots=True)
class RecoveryObservation:
    ok: bool
    message: str
    value: str | None = None
    done: bool = False


class RecoveryEnv:
    def __init__(self, task: RecoveryTask) -> None:
        self.task = task
        self.steps = 0
        self.done = False
        self.completed = False
        self.human_intervention = False
        self.replans = 0
        self.rollbacks = 0
        self.tool_failures = 0
        if task.fault_kind is FaultKind.TOOL_ERROR:
            self.visible_rule = task.corrected_rule
            self.correct_rule = task.corrected_rule
        else:
            self.visible_rule = task.initial_rule
            self.correct_rule = (
                task.initial_rule
                if task.fault_kind is FaultKind.RULE_CHANGE
                else task.corrected_rule
            )
        self._tool_failed = False
        self._rule_changed = False

    def step(self, action: RecoveryAction) -> RecoveryObservation:
        if self.done:
            return RecoveryObservation(True, "episode already finished", done=True)
        self.steps += 1
        if self.steps > self.task.max_steps:
            self.done = True
            return RecoveryObservation(False, "step budget exhausted", done=True)

        if action is RecoveryAction.READ:
            return RecoveryObservation(True, "state read", value=self.visible_rule)

        if action is RecoveryAction.VALIDATE:
            valid = self.visible_rule == self.correct_rule
            return RecoveryObservation(
                valid,
                "state is current" if valid else "state is stale or misleading",
                value=self.visible_rule,
            )

        if action is RecoveryAction.REPLAN:
            self.replans += 1
            self.visible_rule = self.task.corrected_rule
            if self.task.fault_kind is FaultKind.RULE_CHANGE:
                self._rule_changed = True
            self.correct_rule = self.task.corrected_rule
            return RecoveryObservation(True, "replanned from authoritative state")

        if action is RecoveryAction.ROLLBACK:
            self.rollbacks += 1
            return RecoveryObservation(True, "rolled back to checkpoint")

        if action is RecoveryAction.HELP:
            self.human_intervention = True
            self.done = True
            return RecoveryObservation(True, "human intervention requested", done=True)

        if action is RecoveryAction.FINISH:
            self.done = True
            if self.completed:
                return RecoveryObservation(True, "finished", done=True)
            return RecoveryObservation(False, "finish attempted without success", done=True)

        if action is RecoveryAction.ACT:
            if (
                self.task.fault_kind is FaultKind.TOOL_ERROR
                and not self._tool_failed
            ):
                self._tool_failed = True
                self.tool_failures += 1
                return RecoveryObservation(False, "transient tool error")
            if (
                self.task.fault_kind is FaultKind.RULE_CHANGE
                and not self._rule_changed
            ):
                self._rule_changed = True
                self.correct_rule = self.task.corrected_rule
                return RecoveryObservation(False, "environment rule changed")
            if self.visible_rule != self.correct_rule:
                return RecoveryObservation(False, "stale state produced wrong action")
            self.completed = True
            self.done = True
            return RecoveryObservation(True, "task completed", done=True)

        raise ValueError(f"unsupported recovery action: {action!r}")

    def is_success(self) -> bool:
        return self.completed and not self.human_intervention


class RecoveryPolicy:
    """Base class for deterministic recovery action sequences."""

    name = "recovery-policy"
    actions: tuple[RecoveryAction, ...] = ()

    def reset(self) -> None:
        self.index = 0

    def act(self, observation: RecoveryObservation) -> RecoveryAction:
        del observation
        if self.index >= len(self.actions):
            return RecoveryAction.HELP
        action = self.actions[self.index]
        self.index += 1
        return action


class RetryOnlyPolicy(RecoveryPolicy):
    name = "retry-only"
    actions = (
        RecoveryAction.READ,
        RecoveryAction.ACT,
        RecoveryAction.ACT,
        RecoveryAction.FINISH,
    )


class RollbackPolicy(RecoveryPolicy):
    name = "rollback"
    actions = (
        RecoveryAction.READ,
        RecoveryAction.ACT,
        RecoveryAction.ROLLBACK,
        RecoveryAction.ACT,
        RecoveryAction.FINISH,
    )


class ReplanPolicy(RecoveryPolicy):
    name = "replan"
    actions = (
        RecoveryAction.READ,
        RecoveryAction.ACT,
        RecoveryAction.REPLAN,
        RecoveryAction.ACT,
        RecoveryAction.FINISH,
    )


class StateCheckReplanPolicy(RecoveryPolicy):
    name = "state-check-replan"
    actions = (
        RecoveryAction.READ,
        RecoveryAction.VALIDATE,
        RecoveryAction.REPLAN,
        RecoveryAction.ACT,
        RecoveryAction.REPLAN,
        RecoveryAction.ACT,
        RecoveryAction.FINISH,
    )


def generate_recovery_tasks(*, instances: int = 10) -> list[RecoveryTask]:
    if instances < 1:
        raise ValueError("instances must be positive")
    tasks = []
    for kind in FaultKind:
        for instance in range(instances):
            tasks.append(
                RecoveryTask(
                    task_id=f"recovery-{kind.value}-i{instance:02d}",
                    fault_kind=kind,
                    initial_rule="rule-v1",
                    corrected_rule="rule-v2",
                )
            )
    return tasks


def _run_episode(task: RecoveryTask, policy: RecoveryPolicy) -> dict:
    policy.reset()
    env = RecoveryEnv(task)
    observation = RecoveryObservation(True, "start")
    while not observation.done and env.steps <= task.max_steps:
        observation = env.step(policy.act(observation))
    return {
        "task_id": task.task_id,
        "fault_kind": task.fault_kind.value,
        "policy": policy.name,
        "success": env.is_success(),
        "steps": env.steps,
        "human_intervention": env.human_intervention,
        "replans": env.replans,
        "rollbacks": env.rollbacks,
        "tool_failures": env.tool_failures,
        "error": None if env.is_success() else observation.message,
    }


def run_recovery_matrix(tasks: list[RecoveryTask] | None = None) -> dict:
    if tasks is None:
        tasks = generate_recovery_tasks()
    policies = (
        RetryOnlyPolicy(),
        RollbackPolicy(),
        ReplanPolicy(),
        StateCheckReplanPolicy(),
    )
    rows = []
    by_policy: dict[str, dict] = {}
    for policy in policies:
        policy_rows = [_run_episode(task, policy) for task in tasks]
        rows.extend(policy_rows)
        by_fault = {}
        for kind in FaultKind:
            selected = [
                row for row in policy_rows if row["fault_kind"] == kind.value
            ]
            by_fault[kind.value] = {
                "tasks": len(selected),
                "successes": sum(row["success"] for row in selected),
                "success_rate": (
                    sum(row["success"] for row in selected) / len(selected)
                    if selected
                    else 0.0
                ),
            }
        by_policy[policy.name] = {
            "tasks": len(policy_rows),
            "successes": sum(row["success"] for row in policy_rows),
            "success_rate": fmean(
                float(row["success"]) for row in policy_rows
            ),
            "steps": fmean(row["steps"] for row in policy_rows),
            "human_interventions": sum(
                row["human_intervention"] for row in policy_rows
            ),
            "replans": sum(row["replans"] for row in policy_rows),
            "rollbacks": sum(row["rollbacks"] for row in policy_rows),
            "by_fault": by_fault,
        }
    by_fault = {}
    for kind in FaultKind:
        selected = [row for row in rows if row["fault_kind"] == kind.value]
        by_fault[kind.value] = {
            "tasks": len(selected),
            "successes": sum(row["success"] for row in selected),
            "success_rate": (
                fmean(float(row["success"]) for row in selected)
                if selected
                else 0.0
            ),
        }
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "tasks": len(tasks),
        "by_policy": by_policy,
        "by_fault": by_fault,
        "rows": rows,
        "notes": [
            "This is a deterministic recovery state machine, not a model-agent benchmark.",
            "Stale state, misleading documentation, and rule change require replanning.",
        ],
    }
