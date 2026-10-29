import json
from pathlib import Path


def test_frozen_clear_v1_files_exist_and_have_expected_shape():
    root = Path("benchmarks/clear-300-v1")
    tasks = json.loads((root / "tasks.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (root / "split-manifest.json").read_text(encoding="utf-8")
    )
    baselines = json.loads(
        (root / "scripted-baselines.json").read_text(encoding="utf-8")
    )
    assert len(tasks["tasks"]) == 300
    assert manifest["frozen"] is True
    assert manifest["splits"] == {"train": 180, "dev": 60, "test": 60}
    assert baselines["current-rule"]["success_rate"] == 1.0
    assert baselines["sticky-first-rule"]["success_rate"] < 1.0
