import hashlib
import json
import subprocess
import sys
from pathlib import Path

from scripts.audit_portfolio import (
    WORK_PACKAGES,
    _latest_portfolio_entry,
    audit_portfolio,
)


ROOT = Path(__file__).resolve().parents[1]


def test_portfolio_documents_keep_model_and_scientific_boundaries():
    status = (ROOT / "PORTFOLIO-STATUS.md").read_text(encoding="utf-8")
    gate = (ROOT / "MODEL-GATE.md").read_text(encoding="utf-8")
    status_flat = " ".join(status.split())
    assert "## Scientific Boundary" in status
    assert "## Model Gate" in status
    assert "Current decision: HOLD" in gate
    assert "Stop conditions" in gate
    assert "not ready for a model-level capability claim" in status_flat


def test_portfolio_audit_links_and_hashes_are_consistent():
    result = audit_portfolio(ROOT)
    assert result["integrity_ok"] is True, [
        check for check in result["checks"] if not check["ok"]
    ]
    assert set(result["work_packages"]) == set(WORK_PACKAGES)
    assert result["scientific_boundary"]["scientific_result"] is False
    assert result["scientific_boundary"]["model_evaluation_completed"] is False
    assert result["verification"]["self_referential_artifact"] == "portfolio-v4"
    assert result["model_gate"]["status"] in {
        "hold",
        "ready-for-explicit-approval",
    }
    assert all(
        artifact["outputs_match"]
        for artifact in result["artifacts"]
        if not artifact["self_reference"]
    )


def test_manifest_registers_portfolio_audit_artifact():
    manifest = json.loads(
        (ROOT / "research-manifest.json").read_text(encoding="utf-8")
    )
    portfolio = next(
        artifact
        for artifact in manifest["artifacts"]
        if artifact["name"] == "portfolio-v4"
    )
    assert portfolio["latestVersion"] == 1
    assert portfolio["path"] == "artifacts/portfolio-v4/v1/artifact.json"
    assert portfolio["scientific_result"] is False
    assert portfolio["status"] == "portfolio-audit"


def test_latest_portfolio_entry_uses_numeric_family_version():
    manifest = {
        "artifacts": [
            {"name": "portfolio-v1", "latestVersion": 9},
            {"name": "portfolio-v10", "latestVersion": 1},
            {"name": "cpu-program-v0", "latestVersion": 20},
        ]
    }
    assert _latest_portfolio_entry(manifest)["name"] == "portfolio-v10"


def test_audit_check_mode_does_not_rewrite_sealed_outputs():
    outputs = (
        ROOT / "artifacts/portfolio-v4/v1/results/portfolio-audit.json",
        ROOT / "artifacts/portfolio-v4/v1/results/environment-audit.json",
    )
    before = {
        path: (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_mtime_ns,
        )
        for path in outputs
    }
    completed = subprocess.run(
        [sys.executable, "scripts/audit_portfolio.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    after = {
        path: (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_mtime_ns,
        )
        for path in outputs
    }
    assert after == before


def test_artifact_verifier_rejects_changed_output(tmp_path):
    artifact_root = tmp_path / "artifact"
    artifact_root.mkdir()
    output = artifact_root / "result.json"
    output.write_text('{"value": 1}\n', encoding="utf-8")
    expected = hashlib.sha256(output.read_bytes()).hexdigest()
    (artifact_root / "artifact.json").write_text(
        json.dumps({"outputs": {"result.json": expected}}),
        encoding="utf-8",
    )
    output.write_text('{"value": 2}\n', encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "scripts/verify_artifact.py", str(artifact_root)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    result = json.loads(completed.stdout)
    assert result["all_match"] is False
