from longrun.memory.adversarial import run_adversarial_memory_probe


def test_adversarial_memory_distinguishes_trust_rules():
    result = run_adversarial_memory_probe(seed=5, episodes=40)
    policies = result["policies"]
    assert policies["recency"]["poison_event_rate"] == 1.0
    assert policies["source-trust"]["poison_rate"] == 0.0
    assert policies["source-trust"]["poison_event_rate"] == 0.0
    assert policies["source-trust"]["stale_selection_rate"] >= 0.0
    assert result["config"]["episodes"] == 40


def test_adversarial_memory_is_deterministic():
    assert run_adversarial_memory_probe(seed=5, episodes=10) == (
        run_adversarial_memory_probe(seed=5, episodes=10)
    )


def test_adversarial_memory_has_supersession_and_expiry_events():
    result = run_adversarial_memory_probe(seed=5, episodes=4)
    assert result["event_counts"]["expired"] > 0
    assert result["event_counts"]["superseded"] > 0
