"""Deterministic recovery matrix over real temporary files and processes."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


FAULTS = (
    "transient-process",
    "timeout",
    "missing-spec",
    "stale-tree",
    "misleading-doc",
)

_CORRECT_MAPPING = {
    ".txt": "text",
    ".md": "notes",
    ".csv": "tables",
}
_WRONG_MAPPING = {
    ".txt": "tables",
    ".md": "text",
    ".csv": "notes",
}

_WORKER = """
import json
import shutil
import sys
import time
from pathlib import Path

plan_path = Path(sys.argv[1])
control = Path(sys.argv[2])
plan = json.loads(plan_path.read_text(encoding="utf-8"))
attempt_file = control / "attempts.json"
attempts = json.loads(attempt_file.read_text()) if attempt_file.exists() else []
attempts.append(plan["fault"])
attempt_file.write_text(json.dumps(attempts), encoding="utf-8")
if plan["fault"] == "transient-process" and len(attempts) == 1:
    raise SystemExit(3)
if plan["fault"] == "timeout":
    time.sleep(0.3)
for source, destination in plan["moves"].items():
    source_path = Path(source)
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source_path), str(destination_path))
"""


@dataclass(frozen=True, slots=True)
class RecoveryPolicy:
    name: str
    refresh_state: bool
    authoritative_spec: bool
    restore_on_retry: bool
    timeout_seconds: float
    max_attempts: int = 2
    count_replans: bool = False


POLICIES = (
    RecoveryPolicy(
        name="retry-only",
        refresh_state=False,
        authoritative_spec=False,
        restore_on_retry=False,
        timeout_seconds=0.05,
    ),
    RecoveryPolicy(
        name="rollback",
        refresh_state=False,
        authoritative_spec=False,
        restore_on_retry=True,
        timeout_seconds=1.0,
    ),
    RecoveryPolicy(
        name="state-check-replan",
        refresh_state=True,
        authoritative_spec=True,
        restore_on_retry=True,
        timeout_seconds=0.50,
        count_replans=True,
    ),
    RecoveryPolicy(
        name="replan",
        refresh_state=True,
        authoritative_spec=True,
        restore_on_retry=True,
        timeout_seconds=0.50,
        count_replans=True,
    ),
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _route_key(path: str) -> str:
    return PurePosixPath(path).suffix


class RealFaultEnvironment:
    def __init__(self, root: Path, fault: str) -> None:
        if fault not in FAULTS:
            raise ValueError(f"unknown fault: {fault}")
        self.root = root
        self.fault = fault
        self.workspace = root / "workspace"
        self.control = root / "control"
        self.checkpoint = root / "checkpoint"
        self._cached_files: list[str] = []
        self._expected: dict[str, str] = {}
        self._prepare()

    def _prepare(self) -> None:
        self.workspace.mkdir(parents=True)
        self.control.mkdir(parents=True)
        files = {
            "alpha.txt": "alpha",
            "beta.md": "beta",
            "gamma.csv": "id,value\n1,2\n",
        }
        for name, content in files.items():
            path = self.workspace / "inbox" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        (self.workspace / "docs").mkdir()
        (self.workspace / "manifest").mkdir()
        _write_json(
            self.workspace / "docs" / "SPEC.md",
            {"mode": "extension", "map": _CORRECT_MAPPING},
        )
        _write_json(
            self.workspace / "manifest" / "current.json",
            {
                "mode": "extension",
                "mapping": _CORRECT_MAPPING,
                "spec_sha256": "fixture-authoritative-v1",
            },
        )
        self._cached_files = sorted(
            path.name for path in (self.workspace / "inbox").iterdir()
        )
        self._expected = {
            f"sorted/{_CORRECT_MAPPING[_route_key(name)]}/{name}": files[name]
            for name in self._cached_files
        }
        shutil.copytree(self.workspace, self.checkpoint)
        self._inject_fault(files)

    def _inject_fault(self, files: dict[str, str]) -> None:
        if self.fault == "missing-spec":
            (self.workspace / "docs" / "SPEC.md").unlink()
        elif self.fault == "misleading-doc":
            _write_json(
                self.workspace / "docs" / "SPEC.md",
                {"mode": "extension", "map": _WRONG_MAPPING},
            )
        elif self.fault == "stale-tree":
            new_name = "delta.md"
            new_path = self.workspace / "inbox" / new_name
            new_path.write_text("delta", encoding="utf-8")
            self._expected[
                f"sorted/{_CORRECT_MAPPING[_route_key(new_name)]}/{new_name}"
            ] = "delta"

    def _restore(self) -> None:
        inbox = self.workspace / "inbox"
        sorted_dir = self.workspace / "sorted"
        docs = self.workspace / "docs"
        manifest = self.workspace / "manifest"
        for path in (inbox, sorted_dir, docs, manifest):
            if path.exists():
                shutil.rmtree(path)
        for name in ("inbox", "docs", "manifest"):
            shutil.copytree(self.checkpoint / name, self.workspace / name)

    def _scan_files(self, *, refresh: bool) -> list[str]:
        if refresh:
            self._cached_files = sorted(
                path.name for path in (self.workspace / "inbox").iterdir()
            )
        return list(self._cached_files)

    def _mapping(self, *, authoritative: bool) -> dict[str, str]:
        if authoritative:
            payload = json.loads(
                (
                    self.workspace / "manifest" / "current.json"
                ).read_text(encoding="utf-8")
            )
            return payload["mapping"]
        payload = json.loads(
            (self.workspace / "docs" / "SPEC.md").read_text(encoding="utf-8")
        )
        return payload["map"]

    def _expected_files(self) -> dict[str, str]:
        return dict(self._expected)

    def _actual_files(self) -> dict[str, str]:
        root = self.workspace / "sorted"
        if not root.exists():
            return {}
        return {
            path.relative_to(self.workspace).as_posix(): path.read_text(
                encoding="utf-8"
            )
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def _attempt(self, policy: RecoveryPolicy) -> None:
        files = self._scan_files(refresh=policy.refresh_state)
        mapping = self._mapping(authoritative=policy.authoritative_spec)
        moves = {
            str(self.workspace / "inbox" / name): str(
                self.workspace
                / "sorted"
                / mapping[_route_key(name)]
                / name
            )
            for name in files
        }
        plan = self.control / "plan.json"
        _write_json(
            plan,
            {"fault": self.fault, "moves": moves},
        )
        subprocess.run(
            [sys.executable, "-c", _WORKER, str(plan), str(self.control)],
            check=True,
            capture_output=True,
            text=True,
            timeout=policy.timeout_seconds,
        )
        if self._actual_files() != self._expected_files():
            raise RuntimeError("workspace verification failed")

    def execute(self, policy: RecoveryPolicy) -> dict:
        failures: list[str] = []
        rollbacks = 0
        replans = 0
        attempts = 0
        for attempt in range(policy.max_attempts):
            if attempt > 0 and policy.restore_on_retry:
                self._restore()
                rollbacks += 1
            attempts += 1
            try:
                self._attempt(policy)
            except subprocess.TimeoutExpired:
                failures.append("timeout")
            except subprocess.CalledProcessError:
                failures.append("transient-process")
            except (FileNotFoundError, KeyError, RuntimeError):
                failures.append("environment-drift")
            else:
                return {
                    "success": True,
                    "attempts": attempts,
                    "rollbacks": rollbacks,
                    "replans": replans,
                    "failures": failures,
                }
            if policy.count_replans:
                replans += 1
        return {
            "success": False,
            "attempts": attempts,
            "rollbacks": rollbacks,
            "replans": replans,
            "failures": failures,
        }


def run_real_fault_matrix() -> dict:
    rows: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="longrun-real-faults-") as directory:
        root = Path(directory)
        for fault in FAULTS:
            for policy in POLICIES:
                case_root = root / fault / policy.name
                environment = RealFaultEnvironment(case_root, fault)
                result = environment.execute(policy)
                rows.append(
                    {
                        "fault": fault,
                        "policy": policy.name,
                        **result,
                    }
                )
    by_policy = {
        policy.name: {
            "cases": len(FAULTS),
            "successes": sum(
                row["success"]
                for row in rows
                if row["policy"] == policy.name
            ),
            "success_rate": (
                sum(
                    row["success"]
                    for row in rows
                    if row["policy"] == policy.name
                )
                / len(FAULTS)
            ),
            "mean_attempts": (
                sum(row["attempts"] for row in rows if row["policy"] == policy.name)
                / len(FAULTS)
            ),
            "rollbacks": sum(
                row["rollbacks"]
                for row in rows
                if row["policy"] == policy.name
            ),
            "replans": sum(
                row["replans"]
                for row in rows
                if row["policy"] == policy.name
            ),
        }
        for policy in POLICIES
    }
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "config": {
            "faults": len(FAULTS),
            "policies": len(POLICIES),
            "real_filesystem": True,
            "subprocesses": True,
            "network_calls": 0,
        },
        "by_policy": by_policy,
        "rows": rows,
        "notes": [
            "All file operations occur under a temporary directory.",
            "The worker is a short-lived local Python subprocess in the cloud test environment.",
            "This validates recovery mechanics, not model policy quality.",
        ],
        "determinism": "aggregate-only",
    }
