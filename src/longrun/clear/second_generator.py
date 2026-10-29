from __future__ import annotations

import json
import random
from pathlib import PurePosixPath

from .models import FaultSpec, Op, Task


SECOND_FAMILIES = {
    "named_list": {
        "mode": "prefix",
        "variants": (
            {"alpha": "alpha", "beta": "beta", "gamma": "gamma"},
            {"alpha": "north", "beta": "south", "gamma": "east"},
        ),
    },
    "two_part": {
        "mode": "suffix",
        "variants": (
            {"raw": "raw", "final": "final", "draft": "draft"},
            {"raw": "incoming", "final": "released", "draft": "pending"},
        ),
    },
    "typed_record": {
        "mode": "extension",
        "variants": (
            {".txt": "text", ".md": "notes", ".json": "records"},
            {".txt": "prose", ".md": "docs", ".json": "data"},
        ),
    },
}


def _spec(mode: str, mapping: dict[str, str], seed: int) -> str:
    payload = json.dumps(
        {"mode": mode, "map": mapping, "seed": seed},
        sort_keys=True,
        indent=2,
    )
    return (
        "# Second routing specification\n\n"
        "The current rule below supersedes all cached notes. "
        "Routing is based on a named queue, not on the legacy inbox format.\n\n"
        f"<RULE_JSON>\n{payload}\n</RULE_JSON>\n"
    )


def _content_files(family: str, seed: int, variant: int, instance: int) -> dict:
    marker = f"\nseed={seed} variant={variant} instance={instance}\n"
    if family == "named_list":
        return {
            "queue/alpha__one.txt": "alpha one" + marker,
            "queue/beta__two.md": "beta two" + marker,
            "queue/gamma__three.csv": "id,value\n1,2\n" + marker,
        }
    if family == "two_part":
        return {
            "queue/brief__raw.txt": "brief raw" + marker,
            "queue/report__final.md": "report final" + marker,
            "queue/data__draft.json": '{"ok": true}' + marker,
        }
    if family == "typed_record":
        return {
            "queue/record-a.txt": "record a" + marker,
            "queue/readme.md": "readme" + marker,
            "queue/table.json": '{"rows": 2}' + marker,
        }
    raise ValueError(f"unknown family: {family}")


def _route_key(path: str, mode: str) -> str:
    name = PurePosixPath(path).name
    if mode == "prefix":
        return name.split("__", 1)[0]
    if mode == "suffix":
        return PurePosixPath(name).stem.rpartition("__")[2]
    if mode == "extension":
        return PurePosixPath(name).suffix
    raise ValueError(f"unsupported mode: {mode}")


def _make_task(
    *,
    family: str,
    mode: str,
    mapping: dict[str, str],
    variant: int,
    instance: int,
    seed: int,
    fault: bool = False,
    rule_shift: int | None = None,
    tool_fault: int | None = None,
) -> Task:
    files = _content_files(family, seed, variant, instance)
    files["manifest/current.json"] = json.dumps(
        {"family": family, "variant": variant, "source": "current"},
        sort_keys=True,
    )
    files["docs/SPEC.md"] = _spec(mode, mapping, seed)
    expected = {
        path: content
        for path, content in files.items()
        if not path.startswith("queue/")
    }
    for path, content in files.items():
        if not path.startswith("queue/"):
            continue
        key = _route_key(path, mode)
        if key not in mapping:
            raise ValueError(f"no second-generator route for {key!r}")
        expected[f"sorted/{mapping[key]}/{PurePosixPath(path).name}"] = content
    metadata = {
        "generator": "second-v0",
        "format": "named-list",
        "mode": mode,
        "variant": variant,
        "instance": instance,
    }
    if rule_shift is not None:
        metadata["rule_shift"] = rule_shift
    if tool_fault is not None:
        metadata["tool_fault"] = tool_fault
    faults = (FaultSpec(op=Op.MOVE, occurrence=1),) if fault else ()
    task_id = f"second-{family}-v{variant}-i{instance:02d}"
    if rule_shift is not None:
        task_id = f"second-factorial-{family}-rs{rule_shift}-tf{tool_fault}-i{instance:02d}"
    return Task(
        task_id=task_id,
        family_id=f"second_{family}",
        variant=variant,
        instruction=(
            "Route every file under queue/ using docs/SPEC.md. "
            "Preserve the manifest and do not edit file contents."
        ),
        initial_files=files,
        expected_files=expected,
        max_steps=30,
        faults=faults,
        metadata=metadata,
    )


def generate_second_clear_tasks(
    *, instances_per_variant: int = 4, seed: int = 20261028
) -> list[Task]:
    if instances_per_variant < 1:
        raise ValueError("instances_per_variant must be positive")
    rng = random.Random(seed)
    tasks = []
    for family, config in SECOND_FAMILIES.items():
        variants = config["variants"]
        for variant, mapping in enumerate(variants):
            for instance in range(instances_per_variant):
                tasks.append(
                    _make_task(
                        family=family,
                        mode=config["mode"],
                        mapping=mapping,
                        variant=variant,
                        instance=instance,
                        seed=seed + rng.randrange(1000),
                    )
                )
    return tasks


def generate_second_factorial_tasks(
    *, instances_per_variant: int = 4, seed: int = 20261028
) -> list[Task]:
    if instances_per_variant < 1:
        raise ValueError("instances_per_variant must be positive")
    tasks = []
    for family, config in SECOND_FAMILIES.items():
        for rule_shift in (0, 1):
            for tool_fault in (0, 1):
                mapping = config["variants"][rule_shift]
                for instance in range(instances_per_variant):
                    tasks.append(
                        _make_task(
                            family=family,
                            mode=config["mode"],
                            mapping=mapping,
                            variant=rule_shift,
                            instance=instance,
                            seed=seed + instance,
                            fault=bool(tool_fault),
                            rule_shift=rule_shift,
                            tool_fault=tool_fault,
                        )
                    )
    return tasks
