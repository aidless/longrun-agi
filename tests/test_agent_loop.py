from longrun.agent_loop import run_agent_loop_audit


def test_agent_loop_records_replayable_trace_and_resumes():
    result = run_agent_loop_audit(episodes=12, seed=41)
    assert result["episodes"] == 12
    assert result["all_traces_hash_valid"] is True
    assert result["resume_success"] is True
    assert result["duplicate_actions_prevented"] > 0
    assert result["trace_digest"]


def test_agent_loop_is_deterministic():
    first = run_agent_loop_audit(episodes=8, seed=41)
    second = run_agent_loop_audit(episodes=8, seed=41)
    assert first == second
