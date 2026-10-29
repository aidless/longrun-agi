from longrun.memory.provenance import NaiveMemory, ProvenanceMemory
from longrun.memory.scenarios import evaluate_memory_scenarios


def test_provenance_memory_respects_supersession_and_expiry():
    memory = ProvenanceMemory()
    old = memory.add(
        key="rule",
        value="old",
        source="docs/SPEC.md",
        trust=0.9,
        observed_at=1.0,
    )
    current = memory.add(
        key="rule",
        value="current",
        source="docs/SPEC.md",
        trust=0.9,
        observed_at=2.0,
        supersedes=old.record_id,
    )
    expired = memory.add(
        key="rule",
        value="expired",
        source="archive/old.md",
        trust=1.0,
        observed_at=3.0,
        expires_at=4.0,
    )
    selected = memory.best("rule", now=10.0, min_trust=0.5)
    assert selected is not None
    assert selected.record_id == current.record_id
    assert selected.value == "current"
    audit = memory.audit(now=10.0)
    assert expired.record_id in audit["expired"]
    assert old.record_id in audit["invalidated"]


def test_naive_memory_and_provenance_memory_differ_on_poison_suite():
    result = evaluate_memory_scenarios(count=8)
    naive = result["policies"]["recency-only"]
    provenance = result["policies"]["provenance-aware"]
    assert naive["correct_rate"] == 0.0
    assert naive["poison_rate"] == 1.0
    assert provenance["correct_rate"] == 1.0
    assert provenance["poison_rate"] == 0.0


def test_naive_memory_is_explicitly_recency_based():
    memory = NaiveMemory()
    memory.add(key="k", value="old", source="a", trust=1.0, observed_at=1.0)
    memory.add(key="k", value="new", source="b", trust=0.1, observed_at=2.0)
    assert memory.best("k").value == "new"
