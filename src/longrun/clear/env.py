from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import PurePosixPath
from typing import Any

from .models import Action, Observation, Op, Task


def normalize_path(path: str, *, allow_root: bool = False) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path must be a non-empty string")
    candidate = PurePosixPath(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"unsafe path: {path!r}")
    parts = tuple(part for part in candidate.parts if part not in ("", "."))
    if not parts:
        if allow_root:
            return "."
        raise ValueError("root path is not allowed for this action")
    return "/".join(parts)


class FileOpsEnv:
    """A deterministic virtual file system with typed, non-executable actions."""

    def __init__(self, task: Task):
        self.task = task
        self.files: dict[str, str] = {
            normalize_path(path): content for path, content in task.initial_files.items()
        }
        self.expected: dict[str, str] = {
            normalize_path(path): content for path, content in task.expected_files.items()
        }
        self.step_count = 0
        self.done = False
        self.operation_counts: Counter[Op] = Counter()
        self._faults = list(task.faults)
        self._consumed_faults: set[int] = set()
        self.faults_injected: list[str] = []

    def step(self, action: Action) -> Observation:
        if self.done:
            return Observation(True, "episode already finished", step=self.step_count, done=True)
        if self.step_count >= self.task.max_steps:
            self.done = True
            return Observation(
                False,
                "step budget exhausted",
                step=self.step_count,
                done=True,
            )

        self.step_count += 1
        self.operation_counts[action.op] += 1
        fault = self._matching_fault(action.op)
        if fault is not None:
            message = f"{fault.kind}: {fault.message}"
            self.faults_injected.append(message)
            return Observation(
                False,
                message,
                step=self.step_count,
                fault_kind=fault.kind,
            )

        try:
            value = self._dispatch(action)
        except (KeyError, ValueError) as exc:
            return Observation(False, str(exc), step=self.step_count)

        if action.op is Op.FINISH:
            self.done = True
            return Observation(
                True,
                "finished",
                value=self.is_success(),
                step=self.step_count,
                done=True,
            )
        return Observation(True, action.op.value, value=value, step=self.step_count)

    def _matching_fault(self, op: Op):
        occurrence = self.operation_counts[op]
        for index, fault in enumerate(self._faults):
            if index in self._consumed_faults:
                continue
            if fault.op is op and fault.occurrence == occurrence:
                self._consumed_faults.add(index)
                return fault
        return None

    def _dispatch(self, action: Action) -> Any:
        if action.op is Op.FINISH:
            return None
        if action.op is Op.LIST:
            path = normalize_path(action.path or ".", allow_root=True)
            prefix = "" if path == "." else f"{path}/"
            return sorted(
                file_path
                for file_path in self.files
                if file_path.startswith(prefix)
            )
        if action.op is Op.READ:
            path = normalize_path(action.path or "")
            if path not in self.files:
                raise KeyError(f"file not found: {path}")
            return self.files[path]
        if action.op is Op.MOVE:
            src = normalize_path(action.src or "")
            dst = normalize_path(action.dst or "")
            if src not in self.files:
                raise KeyError(f"source not found: {src}")
            if dst in self.files:
                raise ValueError(f"destination exists: {dst}")
            self.files[dst] = self.files.pop(src)
            return dst
        raise ValueError(f"unsupported operation: {action.op}")

    def is_success(self) -> bool:
        return self.files == self.expected

    def snapshot(self) -> dict[str, str]:
        return dict(sorted(self.files.items()))

    def state_digest(self) -> str:
        payload = json.dumps(self.snapshot(), sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
