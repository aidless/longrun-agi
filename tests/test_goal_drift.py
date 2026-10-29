from longrun.probes.goal_drift import run_goal_drift_probe


def test_goal_drift_probe_shows_recency_failure():
    result = run_goal_drift_probe(seed=11, episodes=30, steps=80)
    pinned = result["policies"]["pinned"]
    recency = result["policies"]["recency"]
    assert pinned["final_accuracy"] == 1.0
    assert recency["final_accuracy"] < 1.0
    assert recency["drift_rate"] > 0.0


def test_goal_drift_probe_is_deterministic():
    assert run_goal_drift_probe(seed=11, episodes=10, steps=30) == (
        run_goal_drift_probe(seed=11, episodes=10, steps=30)
    )


def test_goal_drift_episode_contains_trusted_and_ambient_events():
    result = run_goal_drift_probe(seed=11, episodes=4, steps=20)
    assert result["config"]["goal_vocabulary"] >= 4
    assert result["policies"]["pinned"]["correct_steps"] > 0
    assert result["policies"]["decay"]["final_accuracy"] >= 0.0


def test_goal_drift_policies_share_the_same_event_stream():
    result = run_goal_drift_probe(seed=11, episodes=3, steps=10)
    streams = {
        tuple(
            (event["distractor"], event["distractor_strength"])
            for event in result["policies"][name]["example_episode"]["history"]
        )
        for name in ("pinned", "recency", "decay")
    }
    assert len(streams) == 1
