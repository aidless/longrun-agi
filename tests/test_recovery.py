from longrun.clear.recovery import (
    FaultKind,
    RecoveryAction,
    RecoveryEnv,
    RecoveryPolicy,
    generate_recovery_tasks,
    run_recovery_matrix,
)


def test_retry_only_only_recovers_transient_tool_error():
    tasks = generate_recovery_tasks(instances=1)
    result = run_recovery_matrix(tasks)
    rows = result["by_policy"]["retry-only"]["by_fault"]
    assert rows["tool_error"]["success_rate"] == 1.0
    assert rows["stale_state"]["success_rate"] == 0.0
    assert rows["misleading_doc"]["success_rate"] == 0.0
    assert rows["rule_change"]["success_rate"] == 0.0


def test_replan_recovers_each_fault_without_human_intervention():
    result = run_recovery_matrix(generate_recovery_tasks(instances=3))
    replan = result["by_policy"]["replan"]
    assert replan["success_rate"] == 1.0
    assert replan["human_interventions"] == 0
    assert all(row["success_rate"] == 1.0 for row in replan["by_fault"].values())


def test_state_check_replan_does_not_depend_on_stale_finish():
    result = run_recovery_matrix(generate_recovery_tasks(instances=2))
    policy = result["by_policy"]["state-check-replan"]
    assert policy["success_rate"] == 1.0
    assert policy["human_interventions"] == 0
    assert policy["replans"] > 0


def test_recovery_environment_is_deterministic_and_bounded():
    tasks = generate_recovery_tasks(instances=2)
    first = run_recovery_matrix(tasks)
    second = run_recovery_matrix(tasks)
    assert first == second
    assert set(first["by_policy"]) == {
        "retry-only",
        "rollback",
        "replan",
        "state-check-replan",
    }
    assert set(first["by_fault"]) == {kind.value for kind in FaultKind}
    assert all(
        row["steps"] <= task.max_steps
        for task in tasks
        for row in run_recovery_matrix([task])["rows"]
    )


def test_recovery_action_enum_is_explicit():
    assert {action.value for action in RecoveryAction} == {
        "read",
        "act",
        "validate",
        "rollback",
        "replan",
        "help",
        "finish",
    }
    assert isinstance(RecoveryPolicy, type)
    assert isinstance(RecoveryEnv, type)
