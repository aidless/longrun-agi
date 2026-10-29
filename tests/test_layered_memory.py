from longrun.memory.layered import (
    LayeredMemory,
    MemoryLayer,
    run_layered_memory_probe,
)


def test_layered_memory_keeps_layers_separate():
    memory = LayeredMemory()
    memory.add(
        layer="episodic",
        key="last_event",
        value="event-1",
        source="trace",
        trust=0.9,
        observed_at=1.0,
    )
    memory.add(
        layer="semantic",
        key="route",
        value="current",
        source="docs",
        trust=0.9,
        observed_at=1.0,
    )
    memory.add(
        layer="procedural",
        key="route",
        value="current-procedure",
        source="docs",
        trust=0.9,
        observed_at=1.0,
    )
    assert memory.best("route", layer="semantic", now=2.0).value == "current"
    assert (
        memory.best("route", layer="procedural", now=2.0).value
        == "current-procedure"
    )


def test_layered_memory_rejects_low_trust_and_expired_records():
    memory = LayeredMemory()
    good = memory.add(
        layer=MemoryLayer.PROCEDURAL,
        key="route",
        value="safe",
        source="docs/SPEC.md",
        trust=0.95,
        observed_at=1.0,
    )
    memory.add(
        layer=MemoryLayer.PROCEDURAL,
        key="route",
        value="poison",
        source="ambient",
        trust=0.10,
        observed_at=2.0,
    )
    memory.add(
        layer=MemoryLayer.PROCEDURAL,
        key="route",
        value="expired",
        source="archive",
        trust=1.0,
        observed_at=3.0,
        expires_at=4.0,
    )
    assert memory.best("route", layer="procedural", now=5.0).record_id == good.record_id
    audit = memory.audit(now=5.0)
    assert audit["expired"]
    assert audit["low_trust"]


def test_layered_memory_handles_supersession_and_validation():
    memory = LayeredMemory()
    old = memory.add(
        layer="procedural",
        key="route",
        value="old",
        source="docs",
        trust=0.9,
        observed_at=1.0,
    )
    new = memory.add(
        layer="procedural",
        key="route",
        value="new",
        source="docs",
        trust=0.9,
        observed_at=2.0,
        supersedes=old.record_id,
    )
    memory.validate(new.record_id, "task-1")
    assert memory.best("route", layer="procedural", now=3.0).value == "new"
    assert memory.records[1].validated_by == ("task-1",)
    assert old.record_id in memory.audit(now=3.0)["invalidated"]


def test_layered_memory_forgets_expired_and_untrusted_records():
    memory = LayeredMemory()
    memory.add(
        layer="episodic",
        key="event",
        value="expired",
        source="trace",
        trust=0.9,
        observed_at=1.0,
        expires_at=2.0,
    )
    memory.add(
        layer="semantic",
        key="fact",
        value="weak",
        source="ambient",
        trust=0.1,
        observed_at=1.0,
    )
    memory.add(
        layer="semantic",
        key="fact",
        value="kept",
        source="docs",
        trust=0.9,
        observed_at=1.0,
    )
    result = memory.forget(now=3.0, min_trust=0.5)
    assert result["forgotten"] == 2
    assert memory.best("fact", layer="semantic", now=3.0).value == "kept"


def test_layered_memory_probe_has_expected_policy_contrast():
    result = run_layered_memory_probe(seed=13, episodes=20)
    assert result["status"] == "harness-validation"
    assert result["policies"]["flat-rag"]["poison_rate"] > 0.0
    assert result["policies"]["layered-provenance"]["poison_rate"] == 0.0
    assert result["policies"]["layered-provenance"]["final_correct_rate"] == 1.0
    assert result["conflict_cases"] > 0


def test_layered_memory_probe_is_deterministic():
    assert run_layered_memory_probe(seed=13, episodes=10) == (
        run_layered_memory_probe(seed=13, episodes=10)
    )
