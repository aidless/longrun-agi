import json
from pathlib import Path

from longrun.analysis.factorial import DesignError, estimate_factorial


def test_estimate_factorial_accepts_runner_output_shape():
    result = estimate_factorial(
        [
            {
                "task_id": f"t{index}",
                "family_id": f"f{index // 4}",
                "factors": {"x": index % 2, "y": (index // 2) % 2},
                "success": float(index % 3 == 0),
            }
            for index in range(16)
        ],
        ("x", "y"),
        bootstrap_replicates=10,
        seed=1,
    )
    assert result["status"] == "harness-validation"


def test_manifest_records_cpu_program_and_original_points_gap():
    manifest = json.loads(
        Path("research-manifest.json").read_text(encoding="utf-8")
    )
    assert any(
        experiment["id"] == "003-estimator-validity-v0"
        for experiment in manifest["experiments"]
    )
    program = next(
        artifact
        for artifact in manifest["artifacts"]
        if artifact["name"] == "cpu-program-v0"
    )
    assert program["status"] == "harness-validation"
    assert program["scientific_result"] is False
