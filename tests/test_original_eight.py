import json
from pathlib import Path


def test_original_eight_document_maps_user_supplied_points():
    text = Path("ORIGINAL-EIGHT.md").read_text(encoding="utf-8")
    expected = {
        "P1 — Verifier-Gap RL",
        "P2 — FailRecover Agent",
        "P3 — ProvMem",
        "P4 — Calibrated World Model",
        "P5 — Negative-Control Research Agent",
        "P6 — Goal-Drift Probe",
        "P7 — CLEAR-Bench",
        "P8 — Adaptive Compute-Memory Controller",
    }
    assert all(section in text for section in expected)
    assert "Recommended one-person execution order" in text
    assert "Current boundary" in text


def test_program_work_packages_align_with_original_eight_document():
    text = Path("ORIGINAL-EIGHT.md").read_text(encoding="utf-8")
    manifest = json.loads(Path("research-manifest.json").read_text(encoding="utf-8"))
    assert manifest["project"]["status"] == "active"
    assert "cpu-program-v0" in {artifact["name"] for artifact in manifest["artifacts"]}
    assert "P1 — Verifier-Gap RL" in text
