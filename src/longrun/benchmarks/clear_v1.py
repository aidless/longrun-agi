from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import PurePosixPath
from statistics import fmean
from typing import Any


@dataclass(frozen=True, slots=True)
class ClearTask:
    task_id: str
    environment: str
    family_id: str
    variant: int
    instance: int
    split: str
    instruction: str
    initial: dict[str, Any]
    expected: dict[str, Any]
    metadata: dict[str, Any]


def _canonical(payload: object) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _split_for_variant(variant: int) -> str:
    if variant in (0, 1, 2):
        return "train"
    if variant == 3:
        return "dev"
    return "test"


def _spec(mode: str, mapping: dict[str, str], variant: int) -> str:
    rule = json.dumps(
        {"mode": mode, "map": mapping, "variant": variant},
        sort_keys=True,
        indent=2,
    )
    return (
        "# CLEAR-300 rule\n\n"
        "The current rule is authoritative. Cached rules may be stale.\n\n"
        f"<RULE_JSON>\n{rule}\n</RULE_JSON>\n"
    )


FILE_FAMILIES = {
    "file_extension": {
        "mode": "extension",
        "keys": (".txt", ".md", ".csv"),
        "maps": (
            {".txt": "text", ".md": "notes", ".csv": "tables"},
            {".txt": "prose", ".md": "docs", ".csv": "datasets"},
            {".txt": "drafts", ".md": "documentation", ".csv": "sheets"},
            {".txt": "archived", ".md": "reference", ".csv": "exports"},
            {".txt": "incoming", ".md": "public", ".csv": "analysis"},
        ),
    },
    "file_prefix": {
        "mode": "prefix",
        "keys": ("alpha", "beta", "gamma"),
        "maps": (
            {"alpha": "team_a", "beta": "team_b", "gamma": "team_c"},
            {"alpha": "north", "beta": "south", "gamma": "east"},
            {"alpha": "active", "beta": "review", "gamma": "archive"},
            {"alpha": "blue", "beta": "green", "gamma": "red"},
            {"alpha": "intake", "beta": "triage", "gamma": "resolved"},
        ),
    },
    "file_suffix": {
        "mode": "suffix",
        "keys": ("raw", "final", "draft"),
        "maps": (
            {"raw": "incoming", "final": "published", "draft": "review"},
            {"raw": "staging", "final": "released", "draft": "pending"},
            {"raw": "fresh", "final": "done", "draft": "edit"},
            {"raw": "queue", "final": "live", "draft": "hold"},
            {"raw": "unprocessed", "final": "approved", "draft": "working"},
        ),
    },
    "file_tool_rename": {
        "mode": "prefix",
        "keys": ("red", "blue", "green"),
        "maps": (
            {"red": "warm", "blue": "cool", "green": "calm"},
            {"red": "alert", "blue": "observe", "green": "normal"},
            {"red": "priority", "blue": "routine", "green": "deferred"},
            {"red": "urgent", "blue": "monitor", "green": "archive"},
            {"red": "triage", "blue": "review", "green": "closed"},
        ),
    },
    "file_reversed": {
        "mode": "extension",
        "keys": (".txt", ".md", ".csv"),
        "maps": (
            {".txt": "primary", ".md": "secondary", ".csv": "tables"},
            {".txt": "secondary", ".md": "primary", ".csv": "tables"},
            {".txt": "tables", ".md": "primary", ".csv": "secondary"},
            {".txt": "primary", ".md": "tables", ".csv": "secondary"},
            {".txt": "secondary", ".md": "tables", ".csv": "primary"},
        ),
    },
}


def _file_names(family_id: str, mapping: dict[str, str], instance: int) -> dict[str, str]:
    suffix = f"\ninstance={instance}\n"
    if family_id == "file_extension":
        return {
            "inbox/alpha.txt": "alpha" + suffix,
            "inbox/beta.md": "beta" + suffix,
            "inbox/gamma.csv": "id,value\n1,2\n" + suffix,
        }
    if family_id == "file_prefix":
        return {
            "inbox/alpha__one.txt": "alpha one" + suffix,
            "inbox/beta__two.md": "beta two" + suffix,
            "inbox/gamma__three.csv": "id,value\n2,3\n" + suffix,
        }
    if family_id == "file_suffix":
        return {
            "inbox/one__raw.txt": "one raw" + suffix,
            "inbox/two__final.md": "two final" + suffix,
            "inbox/three__draft.csv": "id,value\n3,4\n" + suffix,
        }
    if family_id == "file_tool_rename":
        return {
            "inbox/red__ticket.txt": "red ticket" + suffix,
            "inbox/blue__ticket.md": "blue ticket" + suffix,
            "inbox/green__ticket.csv": "id,value\n4,5\n" + suffix,
        }
    if family_id == "file_reversed":
        return {
            "inbox/one.txt": "one" + suffix,
            "inbox/two.md": "two" + suffix,
            "inbox/three.csv": "id,value\n5,6\n" + suffix,
        }
    raise ValueError(f"unknown file family: {family_id}")


def _route_key(path: str, mode: str) -> str:
    basename = PurePosixPath(path).name
    if mode == "extension":
        return PurePosixPath(basename).suffix
    if mode == "prefix":
        return basename.split("__", 1)[0]
    if mode == "suffix":
        return PurePosixPath(basename).stem.rpartition("__")[2]
    raise ValueError(f"unsupported mode: {mode}")


def _file_task(
    family_id: str,
    family: dict[str, Any],
    variant: int,
    instance: int,
) -> ClearTask:
    mapping = family["maps"][variant]
    files = _file_names(family_id, mapping, instance)
    files["docs/SPEC.md"] = _spec(family["mode"], mapping, variant)
    files["manifest/current.json"] = _canonical(
        {"family": family_id, "variant": variant}
    )
    expected = {
        path: content
        for path, content in files.items()
        if not path.startswith("inbox/")
    }
    for path, content in files.items():
        if not path.startswith("inbox/"):
            continue
        key = _route_key(path, family["mode"])
        expected[f"sorted/{mapping[key]}/{PurePosixPath(path).name}"] = content
    task_id = f"clear-v1-filesystem-{family_id}-v{variant}-i{instance:02d}"
    return ClearTask(
        task_id=task_id,
        environment="filesystem",
        family_id=family_id,
        variant=variant,
        instance=instance,
        split=_split_for_variant(variant),
        instruction=(
            "Route every file under inbox/ according to docs/SPEC.md. "
            "Do not edit or delete content."
        ),
        initial={"files": files},
        expected={"files": expected},
        metadata={"mode": family["mode"], "mapping": mapping},
    )


BROWSER_FAMILIES = {
    "browser_catalog": {
        "options": ("catalog", "search", "cart"),
        "goal": "approved",
        "maps": (
            {"catalog": "review", "search": "approved", "cart": "draft"},
            {"catalog": "approved", "search": "review", "cart": "draft"},
            {"catalog": "draft", "search": "review", "cart": "approved"},
            {"catalog": "approved", "search": "draft", "cart": "review"},
            {"catalog": "review", "search": "draft", "cart": "approved"},
        ),
    },
    "browser_form": {
        "options": ("name", "email", "submit"),
        "goal": "accepted",
        "maps": (
            {"name": "draft", "email": "review", "submit": "accepted"},
            {"name": "accepted", "email": "draft", "submit": "review"},
            {"name": "review", "email": "accepted", "submit": "draft"},
            {"name": "draft", "email": "accepted", "submit": "review"},
            {"name": "review", "email": "draft", "submit": "accepted"},
        ),
    },
    "browser_dashboard": {
        "options": ("overview", "reports", "alerts"),
        "goal": "verified",
        "maps": (
            {"overview": "verified", "reports": "review", "alerts": "draft"},
            {"overview": "review", "reports": "verified", "alerts": "draft"},
            {"overview": "draft", "reports": "verified", "alerts": "review"},
            {"overview": "verified", "reports": "draft", "alerts": "review"},
            {"overview": "review", "reports": "draft", "alerts": "verified"},
        ),
    },
    "browser_ticket": {
        "options": ("open", "pending", "closed"),
        "goal": "accepted",
        "maps": (
            {"open": "review", "pending": "accepted", "closed": "draft"},
            {"open": "accepted", "pending": "review", "closed": "draft"},
            {"open": "draft", "pending": "review", "closed": "accepted"},
            {"open": "review", "pending": "accepted", "closed": "draft"},
            {"open": "review", "pending": "draft", "closed": "accepted"},
        ),
    },
    "browser_docs": {
        "options": ("guide", "api", "changelog"),
        "goal": "verified",
        "maps": (
            {"guide": "draft", "api": "verified", "changelog": "review"},
            {"guide": "verified", "api": "review", "changelog": "draft"},
            {"guide": "review", "api": "draft", "changelog": "verified"},
            {"guide": "draft", "api": "review", "changelog": "verified"},
            {"guide": "verified", "api": "draft", "changelog": "review"},
        ),
    },
}


def _browser_task(
    family_id: str,
    family: dict[str, Any],
    variant: int,
    instance: int,
) -> ClearTask:
    rule = family["maps"][variant]
    options = list(family["options"])
    options = options[instance % len(options):] + options[: instance % len(options)]
    rule_text = _canonical(
        {
            "options": list(family["options"]),
            "rule": rule,
            "goal": family["goal"],
            "variant": variant,
        }
    )
    expected_key = next(key for key, value in rule.items() if value == family["goal"])
    task_id = f"clear-v1-browser-{family_id}-v{variant}-i{instance:02d}"
    return ClearTask(
        task_id=task_id,
        environment="browser",
        family_id=family_id,
        variant=variant,
        instance=instance,
        split=_split_for_variant(variant),
        instruction=(
            "Read docs/BROWSER_RULE.json and submit the option whose "
            "destination equals the current goal."
        ),
        initial={
            "page": "home",
            "options": options,
            "rule_text": rule_text,
            "policy_path": "docs/BROWSER_RULE.json",
            "selected": None,
            "instance_marker": instance,
        },
        expected={"page": "done", "selected": expected_key, "submitted": True},
        metadata={
            "goal": family["goal"],
            "rule": rule,
            "instance_marker": instance,
        },
    )


GRID_FAMILIES = {
    "grid_open": {
        "start": [3, 3],
        "commands": ("north", "east", "south"),
        "maps": (
            {"north": "up", "east": "right", "south": "down"},
            {"north": "right", "east": "down", "south": "left"},
            {"north": "down", "east": "left", "south": "up"},
            {"north": "left", "east": "up", "south": "right"},
            {"north": "up", "east": "left", "south": "right"},
        ),
    },
    "grid_key": {
        "start": [3, 3],
        "commands": ("open", "advance", "stop"),
        "maps": (
            {"open": "right", "advance": "down", "stop": "right"},
            {"open": "down", "advance": "right", "stop": "down"},
            {"open": "right", "advance": "right", "stop": "down"},
            {"open": "down", "advance": "down", "stop": "right"},
            {"open": "up", "advance": "right", "stop": "right"},
        ),
    },
    "grid_corridor": {
        "start": [3, 3],
        "commands": ("one", "two", "three"),
        "maps": (
            {"one": "right", "two": "right", "three": "down"},
            {"one": "right", "two": "down", "three": "right"},
            {"one": "down", "two": "right", "three": "right"},
            {"one": "right", "two": "up", "three": "right"},
            {"one": "left", "two": "right", "three": "down"},
        ),
    },
    "grid_hazard": {
        "start": [3, 3],
        "commands": ("safe", "shift", "finish"),
        "maps": (
            {"safe": "down", "shift": "left", "finish": "down"},
            {"safe": "left", "shift": "down", "finish": "left"},
            {"safe": "down", "shift": "down", "finish": "left"},
            {"safe": "left", "shift": "left", "finish": "down"},
            {"safe": "up", "shift": "left", "finish": "left"},
        ),
    },
    "grid_delay": {
        "start": [3, 3],
        "commands": ("read", "act", "confirm"),
        "maps": (
            {"read": "up", "act": "right", "confirm": "right"},
            {"read": "right", "act": "up", "confirm": "right"},
            {"read": "right", "act": "right", "confirm": "up"},
            {"read": "up", "act": "right", "confirm": "down"},
            {"read": "right", "act": "down", "confirm": "right"},
        ),
    },
}


def _move(position: list[int], direction: str) -> list[int]:
    deltas = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
    }
    dr, dc = deltas[direction]
    return [position[0] + dr, position[1] + dc]


def _grid_expected(
    start: list[int],
    rule: dict[str, str],
    commands: tuple[str, ...],
) -> list[int]:
    position = list(start)
    for command in commands:
        position = _move(position, rule[command])
    return position


def _grid_task(
    family_id: str,
    family: dict[str, Any],
    variant: int,
    instance: int,
) -> ClearTask:
    rule = family["maps"][variant]
    start = list(family["start"])
    base_commands = family["commands"]
    command_sets = (
        (base_commands[0], base_commands[1]),
        (base_commands[1], base_commands[2]),
        (base_commands[2], base_commands[0]),
        (base_commands[0], base_commands[2]),
    )
    commands = command_sets[instance % len(command_sets)]
    expected_position = _grid_expected(start, rule, commands)
    task_id = f"clear-v1-gridworld-{family_id}-v{variant}-i{instance:02d}"
    return ClearTask(
        task_id=task_id,
        environment="gridworld",
        family_id=family_id,
        variant=variant,
        instance=instance,
        split=_split_for_variant(variant),
        instruction=(
            "Read docs/GRID_RULE.json and execute the listed commands "
            "from the current starting position."
        ),
        initial={
            "start": start,
            "size": 7,
            "commands": list(commands),
            "instance_marker": instance,
            "rule_text": _canonical(
                {"rule": rule, "commands": list(commands)}
            ),
            "policy_path": "docs/GRID_RULE.json",
        },
        expected={"position": expected_position, "blocked_hits": 0},
        metadata={"rule": rule, "instance_marker": instance},
    )


def generate_clear_v1_tasks(*, seed: int = 20261028) -> list[ClearTask]:
    if not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    tasks: list[ClearTask] = []
    for family_id, family in FILE_FAMILIES.items():
        for variant in range(5):
            for instance in range(4):
                tasks.append(_file_task(family_id, family, variant, instance))
    for family_id, family in BROWSER_FAMILIES.items():
        for variant in range(5):
            for instance in range(4):
                tasks.append(_browser_task(family_id, family, variant, instance))
    for family_id, family in GRID_FAMILIES.items():
        for variant in range(5):
            for instance in range(4):
                tasks.append(_grid_task(family_id, family, variant, instance))
    return sorted(tasks, key=lambda task: task.task_id)


def _solve_file(task: ClearTask, rule: dict[str, str]) -> dict:
    files = dict(task.initial["files"])
    expected = {
        path: content
        for path, content in files.items()
        if not path.startswith("inbox/")
    }
    for path, content in files.items():
        if not path.startswith("inbox/"):
            continue
        try:
            key = _route_key(path, task.metadata["mode"])
            destination = rule[key]
        except (KeyError, ValueError):
            return {"files": None}
        expected[f"sorted/{destination}/{PurePosixPath(path).name}"] = content
    return {"files": expected}


def _solve_browser(task: ClearTask, rule: dict[str, str]) -> dict:
    goal = task.metadata["goal"]
    selected = next((key for key, value in rule.items() if value == goal), None)
    if selected is None:
        return {"page": "done", "selected": None, "submitted": True}
    return {"page": "done", "selected": selected, "submitted": True}


def _solve_grid(task: ClearTask, rule: dict[str, str]) -> dict:
    position = list(task.initial["start"])
    for command in task.initial["commands"]:
        direction = rule.get(command)
        if direction is None:
            return {"position": None, "blocked_hits": 1}
        position = _move(position, direction)
        size = int(task.initial.get("size", 7))
        if not (0 <= position[0] < size and 0 <= position[1] < size):
            return {"position": position, "blocked_hits": 1}
    return {"position": position, "blocked_hits": 0}


def _solve(task: ClearTask, rule: dict[str, str]) -> dict:
    if task.environment == "filesystem":
        return _solve_file(task, rule)
    if task.environment == "browser":
        return _solve_browser(task, rule)
    return _solve_grid(task, rule)


def verify_task(task: ClearTask) -> bool:
    current_rule = task.metadata["rule"] if "rule" in task.metadata else task.metadata["mapping"]
    return _solve(task, current_rule) == task.expected


def _success_count(rows: list[dict]) -> dict:
    by_environment: dict[str, dict] = {}
    for environment in ("filesystem", "browser", "gridworld"):
        selected = [row for row in rows if row["environment"] == environment]
        successes = sum(row["success"] for row in selected)
        by_environment[environment] = {
            "tasks": len(selected),
            "successes": successes,
            "success_rate": successes / len(selected),
        }
    successes = sum(row["success"] for row in rows)
    return {
        "tasks": len(rows),
        "successes": successes,
        "success_rate": successes / len(rows),
        "by_environment": by_environment,
    }


def run_scripted_baselines(tasks: list[ClearTask]) -> dict:
    current_rows = []
    sticky_rows = []
    first_rule_by_family: dict[str, dict[str, str]] = {}
    for task in tasks:
        current_rule = (
            task.metadata["rule"]
            if "rule" in task.metadata
            else task.metadata["mapping"]
        )
        first_rule_by_family.setdefault(task.family_id, current_rule)
        sticky_rule = first_rule_by_family[task.family_id]
        current_rows.append(
            {
                "task_id": task.task_id,
                "environment": task.environment,
                "success": _solve(task, current_rule) == task.expected,
            }
        )
        sticky_rows.append(
            {
                "task_id": task.task_id,
                "environment": task.environment,
                "success": _solve(task, sticky_rule) == task.expected,
            }
        )
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "current-rule": _success_count(current_rows),
        "sticky-first-rule": _success_count(sticky_rows),
    }


def task_record(task: ClearTask) -> dict:
    return {
        "task_id": task.task_id,
        "environment": task.environment,
        "family_id": task.family_id,
        "variant": task.variant,
        "instance": task.instance,
        "split": task.split,
        "instruction": task.instruction,
        "initial": task.initial,
        "expected": task.expected,
        "metadata": task.metadata,
    }


def task_sha256(task: ClearTask) -> str:
    return hashlib.sha256(
        _canonical(task_record(task)).encode("utf-8")
    ).hexdigest()


def build_split_manifest(
    tasks: list[ClearTask], *, seed: int = 20261028
) -> dict:
    records = [
        {
            **task_record(task),
            "task_sha256": task_sha256(task),
        }
        for task in sorted(tasks, key=lambda task: task.task_id)
    ]
    task_summaries = [
        {
            "task_id": task["task_id"],
            "environment": task["environment"],
            "family_id": task["family_id"],
            "variant": task["variant"],
            "instance": task["instance"],
            "split": task["split"],
            "task_sha256": task["task_sha256"],
        }
        for task in records
    ]
    split_counts = {
        split: sum(task.split == split for task in tasks)
        for split in ("train", "dev", "test")
    }
    environment_counts = {
        environment: sum(task.environment == environment for task in tasks)
        for environment in ("filesystem", "browser", "gridworld")
    }
    canonical_payload = [
        {
            "task_id": task["task_id"],
            "split": task["split"],
            "task_sha256": task["task_sha256"],
        }
        for task in task_summaries
    ]
    canonical_sha256 = hashlib.sha256(
        _canonical(canonical_payload).encode("utf-8")
    ).hexdigest()
    return {
        "schema": 1,
        "name": "clear-300-v1",
        "seed": seed,
        "generator": "longrun.benchmarks.clear_v1",
        "counts": {
            "total": len(tasks),
            "by_environment": environment_counts,
            "by_variant": {
                str(variant): sum(task.variant == variant for task in tasks)
                for variant in range(5)
            },
        },
        "splits": split_counts,
        "frozen": True,
        "tasks": task_summaries,
        "canonical_sha256": canonical_sha256,
    }
