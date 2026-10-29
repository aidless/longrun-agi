from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class Op(str, Enum):
    LIST = "list"
    READ = "read"
    MOVE = "move"
    FINISH = "finish"


@dataclass(frozen=True, slots=True)
class Action:
    op: Op
    path: str | None = None
    src: str | None = None
    dst: str | None = None


@dataclass(frozen=True, slots=True)
class FaultSpec:
    op: Op
    occurrence: int = 1
    kind: str = "transient_error"
    message: str = "injected transient tool failure"


@dataclass(frozen=True, slots=True)
class Task:
    task_id: str
    family_id: str
    variant: int
    instruction: str
    initial_files: Mapping[str, str]
    expected_files: Mapping[str, str]
    max_steps: int = 20
    faults: tuple[FaultSpec, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Observation:
    ok: bool
    message: str
    value: Any = None
    step: int = 0
    done: bool = False
    fault_kind: str | None = None
