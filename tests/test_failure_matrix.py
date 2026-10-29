from longrun.clear.failure_matrix import run_failure_matrix


def test_failure_matrix_distinguishes_recoverable_and_fatal_faults():
    result = run_failure_matrix()
    rows = {row["fault_kind"]: row for row in result["rows"]}
    assert set(rows) == {
        "transient_read",
        "transient_list",
        "transient_move",
        "schema_corruption",
        "missing_source",
    }
    assert rows["transient_read"]["retry_recovers"] is True
    assert rows["transient_move"]["retry_recovers"] is True
    assert rows["schema_corruption"]["retry_recovers"] is False
    assert rows["missing_source"]["retry_recovers"] is False
    assert result["recoverable"] == 3
    assert result["fatal"] == 2


def test_failure_matrix_is_deterministic():
    assert run_failure_matrix() == run_failure_matrix()
