from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from longrun.benchmarks.clear_v1 import (
    build_split_manifest,
    generate_clear_v1_tasks,
    run_scripted_baselines,
    task_record,
    verify_task,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "root",
        type=Path,
        nargs="?",
        default=Path("benchmarks/clear-300-v1"),
    )
    args = parser.parse_args()
    tasks_payload = json.loads(
        (args.root / "tasks.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (args.root / "split-manifest.json").read_text(encoding="utf-8")
    )
    baselines = json.loads(
        (args.root / "scripted-baselines.json").read_text(encoding="utf-8")
    )
    seed = int(tasks_payload["seed"])
    generated = generate_clear_v1_tasks(seed=seed)
    records = [
        {
            **task_record(task),
            "task_sha256": hashlib.sha256(
                json.dumps(
                    task_record(task),
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                ).encode("utf-8")
            ).hexdigest(),
        }
        for task in sorted(generated, key=lambda task: task.task_id)
    ]
    expected_manifest = build_split_manifest(generated, seed=seed)
    expected_baselines = run_scripted_baselines(generated)
    checks = {
        "task_count_300": len(generated) == 300,
        "stored_tasks_match_generator": tasks_payload["tasks"] == records,
        "manifest_matches_generator": manifest == expected_manifest,
        "baselines_match_generator": baselines == expected_baselines,
        "all_current_rule_tasks_verified": all(
            verify_task(task) for task in generated
        ),
        "split_counts": manifest["splits"] == {
            "train": 180,
            "dev": 60,
            "test": 60,
        },
        "environment_counts": manifest["counts"]["by_environment"] == {
            "filesystem": 100,
            "browser": 100,
            "gridworld": 100,
        },
        "canonical_hash_matches": (
            manifest["canonical_sha256"]
            == expected_manifest["canonical_sha256"]
        ),
    }
    result = {
        "root": str(args.root),
        "checks": checks,
        "all_match": all(checks.values()),
        "file_sha256": {
            name: _sha(args.root / name)
            for name in (
                "tasks.json",
                "split-manifest.json",
                "scripted-baselines.json",
            )
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
