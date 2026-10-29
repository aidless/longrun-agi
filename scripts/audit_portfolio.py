from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WORK_PACKAGES = tuple(f"P{index}" for index in range(1, 9))
PORTFOLIO_PREFIX = "portfolio-v"
REQUIRED_DOCS = (
    "README.md",
    "PROGRAM.md",
    "ORIGINAL-EIGHT.md",
    "PORTFOLIO-STATUS.md",
    "MODEL-GATE.md",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _portfolio_sort_key(entry: dict[str, Any]) -> tuple[int, int, str]:
    name = str(entry.get("name", ""))
    suffix = name.removeprefix(PORTFOLIO_PREFIX)
    name_version = int(suffix) if suffix.isdigit() else -1
    try:
        artifact_version = int(entry.get("latestVersion", -1))
    except (TypeError, ValueError):
        artifact_version = -1
    return name_version, artifact_version, name


def _latest_portfolio_entry(
    manifest: dict[str, Any],
) -> dict[str, Any] | None:
    entries = [
        item
        for item in manifest.get("artifacts", [])
        if str(item.get("name", "")).startswith(PORTFOLIO_PREFIX)
    ]
    return max(entries, key=_portfolio_sort_key) if entries else None


def _meminfo_bytes() -> dict[str, int]:
    fields: dict[str, int] = {}
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return fields
    for line in meminfo.read_text(encoding="utf-8").splitlines():
        name, raw_value = line.split(":", 1)
        value = raw_value.strip().split()[0]
        fields[name] = int(value) * 1024
    return fields


def _cpu_model() -> str | None:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.exists():
        return None
    for line in cpuinfo.read_text(encoding="utf-8").splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    return None


def _os_release() -> dict[str, str]:
    release_path = Path("/etc/os-release")
    if not release_path.exists():
        return {}
    fields: dict[str, str] = {}
    for line in release_path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        fields[name] = value.strip().strip('"')
    return fields


def _disk_snapshot(path: Path) -> dict[str, Any]:
    stats = os.statvfs(path)
    total = stats.f_blocks * stats.f_frsize
    free = stats.f_bavail * stats.f_frsize
    used = total - free
    return {
        "path": str(path),
        "total_bytes": total,
        "free_bytes": free,
        "used_bytes": used,
        "used_percent": round((used / total) * 100, 2) if total else None,
    }


def _gpu_snapshot() -> dict[str, Any]:
    devices: list[dict[str, str]] = []
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        command = [
            nvidia_smi,
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=3,
            )
            if completed.returncode == 0:
                for line in completed.stdout.splitlines():
                    parts = [part.strip() for part in line.split(",")]
                    if len(parts) >= 3:
                        devices.append(
                            {
                                "name": parts[0],
                                "memory_total_mib": parts[1],
                                "driver_version": parts[2],
                            }
                        )
        except (OSError, subprocess.SubprocessError):
            pass
    return {
        "nvidia_smi": nvidia_smi,
        "nvidia_device_nodes": {
            "/dev/nvidia0": Path("/dev/nvidia0").exists(),
            "/dev/nvidiactl": Path("/dev/nvidiactl").exists(),
        },
        "devices": devices,
        "count": len(devices),
        "usable_accelerator_established": bool(devices),
    }


def environment_audit(root: Path) -> dict[str, Any]:
    affinity = (
        len(os.sched_getaffinity(0))
        if hasattr(os, "sched_getaffinity")
        else os.cpu_count()
    )
    memory = _meminfo_bytes()
    os_release = _os_release()
    packages = {
        name: importlib.util.find_spec(name) is not None
        for name in ("torch", "transformers", "accelerate", "safetensors")
    }
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "platform": {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "distribution": os_release.get("PRETTY_NAME"),
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        },
        "cpu": {
            "model": _cpu_model(),
            "logical_count": os.cpu_count(),
            "affinity_count": affinity,
        },
        "memory": {
            "total_bytes": memory.get("MemTotal"),
            "available_bytes": memory.get("MemAvailable"),
            "swap_total_bytes": memory.get("SwapTotal"),
        },
        "disk": _disk_snapshot(root),
        "gpu": _gpu_snapshot(),
        "optional_ml_packages": packages,
        "boundary": {
            "audit_read_only": True,
            "model_loaded": False,
            "gpu_job_started": False,
            "network_calls": 0,
            "paid_api_calls": 0,
        },
    }


def _check(check_id: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"id": check_id, "ok": ok, "detail": detail}


def _verify_artifacts(
    root: Path,
    manifest: dict[str, Any],
    self_reference_path: Path | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    artifact_results: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    output_count = 0
    names: set[str] = set()

    for entry in manifest.get("artifacts", []):
        name = entry.get("name", "")
        duplicate = name in names
        names.add(name)
        artifact_path = root / entry.get("path", "")
        exists = artifact_path.is_file()
        checks.append(
            _check(
                f"artifact-exists:{name}",
                exists and not duplicate,
                "artifact exists" if exists else f"missing: {artifact_path}",
            )
        )
        if not exists:
            continue

        artifact = _load_json(artifact_path)
        version_ok = (
            artifact.get("name") == name
            and artifact.get("version") == entry.get("latestVersion")
            and artifact_path.parent.name == f"v{entry.get('latestVersion')}"
        )
        checks.append(
            _check(
                f"artifact-version:{name}",
                version_ok,
                (
                    f"name={artifact.get('name')}, version={artifact.get('version')}, "
                    f"path={_relative(artifact_path, root)}"
                ),
            )
        )

        # The portfolio report cannot hash itself without becoming unstable.
        # Its two outputs are verified by the external artifact verifier.
        if (
            self_reference_path is not None
            and artifact_path.resolve() == self_reference_path.resolve()
        ):
            checks.append(
                _check(
                    f"portfolio-self-verification:{name}",
                    True,
                    "self-referential outputs delegated to scripts/verify_artifact.py",
                )
            )
            artifact_results.append(
                {
                    "name": name,
                    "path": _relative(artifact_path, root),
                    "version": artifact.get("version"),
                    "status": artifact.get("status"),
                    "scientific_result": artifact.get("scientific_result"),
                    "outputs_match": None,
                    "self_reference": True,
                    "outputs": [],
                }
            )
            continue

        output_checks: list[dict[str, Any]] = []
        for relative_output, expected in artifact.get("outputs", {}).items():
            output_count += 1
            output_path = artifact_path.parent / relative_output
            actual = sha256_file(output_path) if output_path.is_file() else None
            output_checks.append(
                {
                    "path": relative_output,
                    "expected": expected,
                    "actual": actual,
                    "match": actual == expected,
                }
            )
        outputs_match = bool(output_checks) and all(
            item["match"] for item in output_checks
        )
        checks.append(
            _check(
                f"artifact-outputs:{name}",
                outputs_match,
                f"{sum(item['match'] for item in output_checks)}/"
                f"{len(output_checks)} output hashes match",
            )
        )
        artifact_results.append(
            {
                "name": name,
                "path": _relative(artifact_path, root),
                "version": artifact.get("version"),
                "status": artifact.get("status"),
                "scientific_result": artifact.get("scientific_result"),
                "outputs_match": outputs_match,
                "self_reference": False,
                "outputs": output_checks,
            }
        )
    return artifact_results, checks, output_count


def _document_checks(root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for relative_path in REQUIRED_DOCS:
        path = root / relative_path
        checks.append(
            _check(
                f"document:{relative_path}",
                path.is_file() and bool(path.read_text(encoding="utf-8").strip()),
                "present and non-empty" if path.is_file() else "missing",
            )
        )

    original_eight_path = root / "ORIGINAL-EIGHT.md"
    original_eight = (
        original_eight_path.read_text(encoding="utf-8")
        if original_eight_path.is_file()
        else ""
    )
    missing_packages = [
        package for package in WORK_PACKAGES if f"## {package}" not in original_eight
    ]
    checks.append(
        _check(
            "original-eight-mapping",
            not missing_packages,
            "P1-P8 mapped"
            if not missing_packages
            else f"missing sections: {', '.join(missing_packages)}",
        )
    )

    status_path = root / "PORTFOLIO-STATUS.md"
    status_text = (
        status_path.read_text(encoding="utf-8") if status_path.is_file() else ""
    )
    status_tokens = (
        "## Scientific Boundary",
        "## Model Gate",
        "Reproduction",
        "P1",
        "P8",
    )
    missing_status_tokens = [
        token for token in status_tokens if token not in status_text
    ]
    checks.append(
        _check(
            "portfolio-status-sections",
            not missing_status_tokens,
            "required sections present"
            if not missing_status_tokens
            else f"missing: {', '.join(missing_status_tokens)}",
        )
    )

    model_gate_path = root / "MODEL-GATE.md"
    model_gate = (
        model_gate_path.read_text(encoding="utf-8")
        if model_gate_path.is_file()
        else ""
    )
    gate_tokens = (
        "Current decision: HOLD",
        "Model artifact",
        "Offline and network",
        "Evaluation contract",
        "Stop conditions",
        "Approval checklist",
    )
    missing_gate_tokens = [token for token in gate_tokens if token not in model_gate]
    checks.append(
        _check(
            "model-gate-sections",
            not missing_gate_tokens,
            "required sections present"
            if not missing_gate_tokens
            else f"missing: {', '.join(missing_gate_tokens)}",
        )
    )
    return checks


def _manifest_checks(
    root: Path,
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    project = manifest.get("project", {})
    checks.append(
        _check(
            "project-active",
            project.get("status") == "active",
            f"status={project.get('status')}",
        )
    )

    experiment_ids = [item.get("id") for item in manifest.get("experiments", [])]
    checks.append(
        _check(
            "experiment-ids-unique",
            len(experiment_ids) == len(set(experiment_ids)),
            f"{len(experiment_ids)} experiments",
        )
    )

    missing_experiment_files: list[str] = []
    for experiment in manifest.get("experiments", []):
        for field in ("design", "log"):
            relative_path = experiment.get(field)
            if relative_path and not (root / relative_path).is_file():
                missing_experiment_files.append(relative_path)
    checks.append(
        _check(
            "experiment-files-exist",
            not missing_experiment_files,
            "all design/log files present"
            if not missing_experiment_files
            else f"missing: {', '.join(missing_experiment_files)}",
        )
    )

    history = manifest.get("loop", {}).get("history", [])
    missing_history_artifacts = [
        item["artifact"]
        for item in history
        if item.get("artifact") and not (root / item["artifact"]).is_file()
    ]
    checks.append(
        _check(
            "history-artifacts-exist",
            not missing_history_artifacts,
            "all loop-history artifacts present"
            if not missing_history_artifacts
            else f"missing: {', '.join(missing_history_artifacts)}",
        )
    )

    portfolio_entries = [
        item
        for item in manifest.get("artifacts", [])
        if str(item.get("name", "")).startswith(PORTFOLIO_PREFIX)
    ]
    selected = _latest_portfolio_entry(manifest)
    checks.append(
        _check(
            "portfolio-artifact-registered",
            selected is not None and len(portfolio_entries) == len(
                {item.get("name") for item in portfolio_entries}
            ),
            (
                f"latest={selected.get('name')}; "
                f"{len(portfolio_entries)} manifest entries"
                if selected is not None
                else "no portfolio artifact registered"
            ),
        )
    )
    return checks


def _program_checks(
    root: Path,
    manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entry = next(
        (
            item
            for item in manifest.get("artifacts", [])
            if item.get("name") == "cpu-program-v0"
        ),
        None,
    )
    if entry is None:
        return (
            [_check("cpu-program-registered", False, "cpu-program-v0 missing")],
            {},
        )
    artifact_path = root / entry["path"]
    artifact = _load_json(artifact_path)
    statuses = artifact.get("work_package_status", {})
    package_keys = set(statuses)
    checks = [
        _check(
            "cpu-program-eight-packages",
            package_keys == set(WORK_PACKAGES),
            f"packages={','.join(sorted(package_keys))}",
        ),
        _check(
            "cpu-program-scientific-boundary",
            artifact.get("scientific_result") is False
            and artifact.get("novelty_status") == "not-established",
            "scientific_result=false, novelty_status=not-established",
        ),
    ]
    return checks, statuses


def _portfolio_input_checks(
    root: Path,
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    entry = _latest_portfolio_entry(manifest)
    if entry is None:
        return [_check("portfolio-source-hashes", False, "entry missing")]
    artifact_path = root / entry["path"]
    if not artifact_path.is_file():
        return [_check("portfolio-source-hashes", False, "artifact missing")]

    artifact = _load_json(artifact_path)
    source_hashes = artifact.get("inputs", {}).get("source_sha256", {})
    mismatches: list[str] = []
    for relative_path, expected in source_hashes.items():
        source_path = root / relative_path
        actual = sha256_file(source_path) if source_path.is_file() else None
        if actual != expected:
            mismatches.append(relative_path)
    return [
        _check(
            "portfolio-source-hashes",
            bool(source_hashes) and not mismatches,
            f"{len(source_hashes) - len(mismatches)}/{len(source_hashes)} source hashes match",
        )
    ]


def audit_portfolio(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest = _load_json(root / "research-manifest.json")
    environment = environment_audit(root)
    portfolio_entry = _latest_portfolio_entry(manifest)
    self_reference_path = (
        root / portfolio_entry["path"] if portfolio_entry is not None else None
    )

    checks = _document_checks(root)
    artifact_results, artifact_checks, output_count = _verify_artifacts(
        root, manifest, self_reference_path
    )
    checks.extend(artifact_checks)
    checks.extend(_manifest_checks(root, manifest))
    program_checks, work_package_status = _program_checks(root, manifest)
    checks.extend(program_checks)
    checks.extend(_portfolio_input_checks(root, manifest))

    scientific_results = [
        item["name"]
        for item in artifact_results
        if item["scientific_result"] is not False
    ]
    checks.append(
        _check(
            "scientific-claims-not-promoted",
            not scientific_results,
            "all artifacts retain scientific_result=false"
            if not scientific_results
            else f"unexpected scientific results: {', '.join(scientific_results)}",
        )
    )

    model_gate = manifest.get("model_gate", {})
    approval = model_gate.get("approval_status")
    capacity_preflight = model_gate.get("capacity_preflight", {})
    capacity_status = capacity_preflight.get("status", "not-measured")
    gate_reasons: list[str] = []
    if approval != "approved":
        gate_reasons.append("No approved model-download/runtime record in manifest")
    if capacity_status != "passed":
        gate_reasons.append(
            "No passed model-capacity preflight for the exact cloud target"
        )
    model_gate_status = "hold" if gate_reasons else "ready-for-explicit-approval"

    integrity_ok = all(item["ok"] for item in checks)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "id": manifest.get("project", {}).get("id"),
            "title": manifest.get("project", {}).get("title"),
            "phase": manifest.get("loop", {}).get("phase"),
            "iteration": manifest.get("loop", {}).get("iteration"),
        },
        "status": "pass" if integrity_ok else "fail",
        "integrity_ok": integrity_ok,
        "counts": {
            "documents": len(REQUIRED_DOCS),
            "experiments": len(manifest.get("experiments", [])),
            "artifacts": len(manifest.get("artifacts", [])),
            "verified_outputs": output_count,
            "work_packages": len(work_package_status),
            "checks": len(checks),
            "checks_passed": sum(item["ok"] for item in checks),
        },
        "work_packages": {
            package: {"status": work_package_status.get(package)}
            for package in WORK_PACKAGES
        },
        "artifacts": artifact_results,
        "verification": {
            "self_referential_artifact": (
                portfolio_entry.get("name") if portfolio_entry is not None else None
            ),
            "self_outputs_verified_by": "scripts/verify_artifact.py",
        },
        "model_gate": {
            "status": model_gate_status,
            "approval_status": approval,
            "capacity_preflight_status": capacity_status,
            "capacity_preflight_scope": capacity_preflight.get(
                "scope",
                "exact cloud execution target",
            ),
            "reasons": gate_reasons,
            "document": "MODEL-GATE.md",
            "environment_snapshot_role": "execution-host context only",
        },
        "scientific_boundary": {
            "scientific_result": False,
            "novelty_status": "not-established",
            "model_evaluation_completed": False,
            "external_benchmark_completed": False,
        },
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit LongRun-AGI portfolio integrity and environment capacity."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--environment-output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--fail-on-blocked-model-gate",
        action="store_true",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Audit without rewriting the recorded output files.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    manifest = _load_json(root / "research-manifest.json")
    portfolio_entry = _latest_portfolio_entry(manifest)
    if portfolio_entry is None:
        print("no portfolio artifact registered in research-manifest.json")
        return 1
    portfolio_artifact = root / portfolio_entry["path"]
    default_results = portfolio_artifact.parent / "results"
    output = (
        (args.output if args.output.is_absolute() else root / args.output)
        if args.output is not None
        else default_results / "portfolio-audit.json"
    )
    environment_output = (
        (
            args.environment_output
            if args.environment_output.is_absolute()
            else root / args.environment_output
        )
        if args.environment_output is not None
        else default_results / "environment-audit.json"
    )

    result = audit_portfolio(root)
    environment = environment_audit(root)
    if not args.check:
        _write_json(output, result)
        _write_json(environment_output, environment)

    summary = {
        "status": result["status"],
        "integrity_ok": result["integrity_ok"],
        "counts": result["counts"],
        "model_gate": result["model_gate"]["status"],
        "output": _relative(output, root),
        "environment_output": _relative(environment_output, root),
        "check_only": args.check,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

    if not result["integrity_ok"]:
        return 1
    if args.fail_on_blocked_model_gate and result["model_gate"]["status"] != (
        "ready-for-explicit-approval"
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
