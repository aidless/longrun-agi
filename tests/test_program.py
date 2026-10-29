from longrun.program import run_cpu_program


def test_cpu_program_covers_all_eight_current_work_packages():
    result = run_cpu_program(quick=True)
    assert result["status"] == "harness-validation"
    assert result["scientific_result"] is False
    assert set(result["work_packages"]) == {
        "P1",
        "P2",
        "P3",
        "P4",
        "P5",
        "P6",
        "P7",
        "P8",
    }
    assert result["summary"]["completed_cpu_probes"] == 8
    assert result["summary"]["gpu_used"] is False


def test_cpu_program_is_deterministic():
    first = run_cpu_program(quick=True)
    second = run_cpu_program(quick=True)
    first.pop("generated_at", None)
    second.pop("generated_at", None)
    assert first == second


def test_program_marks_permanent_faults_as_not_recovered():
    result = run_cpu_program(quick=True)
    rows = {
        row["fault_kind"]: row
        for row in result["work_packages"]["P2"]["evidence"]["failure_matrix"]
    }
    assert rows["schema_corruption"]["retry_success"] is False
    assert rows["missing_source"]["retry_success"] is False
