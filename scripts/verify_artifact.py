from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def verify(root: Path) -> dict:
    artifact_path = root / "artifact.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    checks: list[dict] = []
    for relative_path, expected in artifact["outputs"].items():
        path = root / relative_path
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        checks.append(
            {
                "path": relative_path,
                "expected": expected,
                "actual": actual,
                "match": actual == expected,
            }
        )
    return {
        "artifact": str(artifact_path),
        "checks": checks,
        "all_match": all(check["match"] for check in checks),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    result = verify(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
