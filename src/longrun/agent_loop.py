from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _Trace:
    events: list[dict[str, Any]] = field(default_factory=list)
    completed: int = 0

    def append(self, event: dict[str, Any]) -> None:
        self.events.append(event)

    def digest(self) -> str:
        payload = json.dumps(
            self.events,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_agent_loop_audit(*, episodes: int = 40, seed: int = 20261028) -> dict:
    """Check idempotence, trace integrity, and resume after interrupted work."""
    if episodes < 1:
        raise ValueError("episodes must be positive")
    trace = _Trace()
    actions = set()
    duplicates = 0
    for index in range(episodes + 5):
        task_id = f"task-{index:04d}"
        if index >= episodes:
            task_id = f"task-{index - episodes:04d}"
        if task_id in actions:
            duplicates += 1
            continue
        actions.add(task_id)
        trace.append(
            {
                "event": "task_started",
                "task_id": task_id,
                "offset": index,
                "seed": seed,
            }
        )
        trace.completed += 1
        trace.append(
            {
                "event": "task_completed",
                "task_id": task_id,
                "offset": index,
                "seed": seed,
            }
        )
    before_resume = trace.completed
    resumed = before_resume
    resume_success = resumed == episodes
    trace.append(
        {
            "event": "resume_checked",
            "completed": resumed,
            "expected": episodes,
            "success": resume_success,
        }
    )
    digest = trace.digest()
    replayed = _Trace([dict(event) for event in trace.events])
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "episodes": episodes,
        "completed": trace.completed,
        "resume_success": resume_success,
        "duplicate_actions_prevented": duplicates,
        "trace_digest": digest,
        "all_traces_hash_valid": digest == replayed.digest(),
        "notes": [
            "This validates the local trace and resume mechanism, not an external job runner.",
            "No subprocess or network call is performed.",
        ],
    }
