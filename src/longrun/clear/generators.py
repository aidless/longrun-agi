from __future__ import annotations

import json
from pathlib import PurePosixPath

from .models import FaultSpec, Op, Task


RULE_BEGIN = "<RULE_JSON>"
RULE_END = "</RULE_JSON>"

FAMILIES = {
    "extension_sort": {
        "mode": "extension",
        "variants": (
            {".txt": "text", ".md": "notes", ".csv": "tables", ".log": "logs"},
            {".txt": "prose", ".md": "documentation", ".csv": "datasets", ".log": "traces"},
            {".txt": "documents", ".md": "docs", ".csv": "spreadsheets", ".log": "diagnostics"},
        ),
    },
    "prefix_route": {
        "mode": "prefix",
        "variants": (
            {"alpha": "team_a", "beta": "team_b", "gamma": "team_c"},
            {"alpha": "north", "beta": "south", "gamma": "east"},
            {"alpha": "archive", "beta": "active", "gamma": "review"},
        ),
    },
    "suffix_route": {
        "mode": "suffix",
        "variants": (
            {"raw": "incoming", "final": "published", "draft": "review"},
            {"raw": "unprocessed", "final": "released", "draft": "pending"},
            {"raw": "staging", "final": "production", "draft": "editorial"},
        ),
    },
}


def _spec(mode: str, mapping: dict[str, str], variant: int) -> str:
    rule = json.dumps({"mode": mode, "map": mapping}, sort_keys=True, indent=2)
    return (
        "# Routing specification\n\n"
        f"Version: v{variant + 1}\n\n"
        "Read this file before acting. The current routing rule is authoritative; "
        "old notes and cached rules may be stale.\n\n"
        f"{RULE_BEGIN}\n{rule}\n{RULE_END}\n"
    )


def _inbox_files(family: str, instance: int) -> dict[str, str]:
    suffix = f" instance={instance}\n"
    if family == "extension_sort":
        return {
            "inbox/alpha.txt": "alpha content\n" + suffix,
            "inbox/beta.md": "beta content\n" + suffix,
            "inbox/gamma.csv": "id,value\n1,2\n" + suffix,
            "inbox/delta.txt": "delta content\n" + suffix,
            "inbox/epsilon.log": "event=ok\n" + suffix,
        }
    if family == "prefix_route":
        return {
            "inbox/alpha__report.txt": "alpha report\n" + suffix,
            "inbox/alpha__notes.md": "alpha notes\n" + suffix,
            "inbox/beta__table.csv": "id,value\n2,3\n" + suffix,
            "inbox/beta__trace.log": "event=beta\n" + suffix,
            "inbox/gamma__draft.md": "gamma draft\n" + suffix,
            "inbox/gamma__data.csv": "id,value\n4,5\n" + suffix,
        }
    if family == "suffix_route":
        return {
            "inbox/report__raw.txt": "report raw\n" + suffix,
            "inbox/summary__final.md": "summary final\n" + suffix,
            "inbox/table__raw.csv": "id,value\n6,7\n" + suffix,
            "inbox/notes__draft.md": "notes draft\n" + suffix,
            "inbox/data__final.csv": "id,value\n8,9\n" + suffix,
            "inbox/debug__draft.log": "event=debug\n" + suffix,
        }
    raise ValueError(f"unknown family: {family}")


def _route_key(path: str, mode: str) -> str:
    basename = PurePosixPath(path).name
    if mode == "extension":
        return PurePosixPath(basename).suffix
    if mode == "prefix":
        return basename.split("__", 1)[0]
    if mode == "suffix":
        stem = PurePosixPath(basename).stem
        return stem.rpartition("__")[2]
    raise ValueError(f"unsupported mode: {mode}")


def _make_task(
    *,
    family_id: str,
    content_family: str | None = None,
    mode: str,
    mapping: dict[str, str],
    variant: int,
    instance: int,
    faults: tuple[FaultSpec, ...] = (),
    max_steps: int = 30,
    task_tag: str | None = None,
    extra_metadata: dict | None = None,
    memory_mapping: dict[str, str] | None = None,
    memory_poison: bool = False,
) -> Task:
    content_family = content_family or family_id
    spec = _spec(mode, mapping, variant)
    initial = {"docs/SPEC.md": spec}
    initial.update(_inbox_files(content_family, instance))
    if memory_mapping is not None:
        initial["memory/routing-note.json"] = json.dumps(
            {
                "key": "routing-rule",
                "value": {"mode": mode, "map": memory_mapping},
                "source": "user-note.txt" if memory_poison else "docs/SPEC.md",
                "trust": 0.10 if memory_poison else 0.95,
                "observed_at": 5.0 if memory_poison else 4.0,
                "poisoned": memory_poison,
            },
            sort_keys=True,
            indent=2,
        ) + "\n"
    expected = {
        path: content
        for path, content in initial.items()
        if not path.startswith("inbox/")
    }
    for path, content in initial.items():
        if not path.startswith("inbox/"):
            continue
        key = _route_key(path, mode)
        if key not in mapping:
            raise ValueError(f"no route for {key!r} in family {family_id}")
        basename = PurePosixPath(path).name
        destination = f"sorted/{mapping[key]}/{basename}"
        expected[destination] = content
    task_id = task_tag or f"{family_id}-v{variant}-i{instance:02d}"
    metadata = {"mode": mode, "variant": variant, "instance": instance}
    if memory_mapping is not None:
        metadata["memory_poison"] = int(memory_poison)
    if extra_metadata:
        metadata.update(extra_metadata)
    return Task(
        task_id=task_id,
        family_id=family_id,
        variant=variant,
        instruction=(
            "Sort every file under inbox/ using the current docs/SPEC.md rule. "
            "Do not delete, edit, or duplicate file contents."
        ),
        initial_files=initial,
        expected_files=expected,
        max_steps=max_steps,
        faults=faults,
        metadata=metadata,
    )


def generate_tasks(instances_per_variant: int = 4) -> list[Task]:
    if instances_per_variant < 1:
        raise ValueError("instances_per_variant must be positive")
    tasks: list[Task] = []
    for family_id, config in FAMILIES.items():
        for variant, mapping in enumerate(config["variants"]):
            for instance in range(instances_per_variant):
                tasks.append(
                    _make_task(
                        family_id=family_id,
                        content_family=family_id,
                        mode=config["mode"],
                        mapping=mapping,
                        variant=variant,
                        instance=instance,
                    )
                )
    return tasks


def generate_fault_tasks() -> list[Task]:
    mapping = FAMILIES["extension_sort"]["variants"][0]
    return [
        _make_task(
            family_id="fault_recovery",
            content_family="extension_sort",
            mode="extension",
            mapping=mapping,
            variant=0,
            instance=100,
            faults=(FaultSpec(op=Op.READ, occurrence=1),),
        ),
        _make_task(
            family_id="fault_recovery",
            content_family="extension_sort",
            mode="extension",
            mapping=mapping,
            variant=1,
            instance=101,
            faults=(FaultSpec(op=Op.MOVE, occurrence=1),),
        ),
    ]


def generate_factorial_tasks(instances_per_variant: int = 4) -> list[Task]:
    """Generate a 2x2 rule-shift x tool-fault design for failure attribution."""
    if instances_per_variant < 1:
        raise ValueError("instances_per_variant must be positive")
    tasks: list[Task] = []
    for content_family, config in FAMILIES.items():
        for rule_shift in (0, 1):
            for tool_fault in (0, 1):
                faults = (
                    (FaultSpec(op=Op.MOVE, occurrence=1),)
                    if tool_fault
                    else ()
                )
                for instance in range(instances_per_variant):
                    task_tag = (
                        f"factorial-{content_family}-"
                        f"rs{rule_shift}-tf{tool_fault}-i{instance:02d}"
                    )
                    tasks.append(
                        _make_task(
                            family_id=f"factorial_{content_family}",
                            content_family=content_family,
                            mode=config["mode"],
                            mapping=config["variants"][rule_shift],
                            variant=rule_shift,
                            instance=instance,
                            faults=faults,
                            task_tag=task_tag,
                            extra_metadata={
                                "rule_shift": rule_shift,
                                "tool_fault": tool_fault,
                            },
                        )
                    )
    return tasks


def generate_three_factor_tasks(instances_per_variant: int = 4) -> list[Task]:
    """Generate rule-shift x tool-fault x memory-poison tasks."""
    if instances_per_variant < 1:
        raise ValueError("instances_per_variant must be positive")
    tasks: list[Task] = []
    for content_family, config in FAMILIES.items():
        for rule_shift in (0, 1):
            mapping = config["variants"][rule_shift]
            poison_mapping = config["variants"][1 - rule_shift]
            for tool_fault in (0, 1):
                faults = (
                    (FaultSpec(op=Op.MOVE, occurrence=1),)
                    if tool_fault
                    else ()
                )
                for memory_poison in (0, 1):
                    note_mapping = poison_mapping if memory_poison else mapping
                    for instance in range(instances_per_variant):
                        task_tag = (
                            f"three-factor-{content_family}-"
                            f"rs{rule_shift}-tf{tool_fault}-"
                            f"mp{memory_poison}-i{instance:02d}"
                        )
                        tasks.append(
                            _make_task(
                                family_id=f"three_factor_{content_family}",
                                content_family=content_family,
                                mode=config["mode"],
                                mapping=mapping,
                                variant=rule_shift,
                                instance=instance,
                                faults=faults,
                                task_tag=task_tag,
                                extra_metadata={
                                    "rule_shift": rule_shift,
                                    "tool_fault": tool_fault,
                                    "memory_poison": memory_poison,
                                },
                                memory_mapping=note_mapping,
                                memory_poison=bool(memory_poison),
                            )
                        )
    return tasks
