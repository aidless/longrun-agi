from longrun.memory.layered import MemoryLayer
from longrun.memory.sqlite_store import (
    MemoryMutation,
    SQLiteMemoryStore,
    run_persistent_memory_probe,
)


def test_store_survives_reopen(tmp_path):
    path = tmp_path / "memory.sqlite3"
    with SQLiteMemoryStore(path) as store:
        record = store.add(
            layer="semantic",
            key="route",
            value="safe",
            source="docs/current.json",
            trust=0.95,
            observed_at=1.0,
        )
        assert record.record_id == "persistent-000001"

    with SQLiteMemoryStore(path) as reopened:
        selected = reopened.best("route", layer="semantic", now=2.0)
        assert selected is not None
        assert selected.value == "safe"
        assert selected.source == "docs/current.json"


def test_batch_mutation_rolls_back_on_invalid_record(tmp_path):
    with SQLiteMemoryStore(tmp_path / "memory.sqlite3") as store:
        before = store.audit(now=1.0)["records"]
        try:
            store.apply_batch(
                [
                    MemoryMutation(
                        layer="semantic",
                        key="rollback",
                        value="first",
                        source="test",
                        trust=0.9,
                        observed_at=1.0,
                    ),
                    MemoryMutation(
                        layer="semantic",
                        key="rollback",
                        value="invalid",
                        source="test",
                        trust=1.5,
                        observed_at=2.0,
                    ),
                ]
            )
        except ValueError as exc:
            assert "trust" in str(exc)
        else:
            raise AssertionError("invalid batch must fail")
        assert store.audit(now=1.0)["records"] == before


def test_conflict_and_supersession(tmp_path):
    with SQLiteMemoryStore(tmp_path / "memory.sqlite3") as store:
        first = store.add(
            layer="procedural",
            key="route",
            value="north",
            source="docs/a.md",
            trust=0.9,
            observed_at=1.0,
        )
        second = store.add(
            layer="procedural",
            key="route",
            value="south",
            source="docs/b.md",
            trust=0.9,
            observed_at=2.0,
        )
        assert len(
            store.conflicts("route", layer="procedural", now=3.0)
        ) == 2
        store.add(
            layer="procedural",
            key="route",
            value="north",
            source="docs/current.md",
            trust=0.95,
            observed_at=3.0,
            supersedes=first.record_id,
        )
        remaining_conflicts = store.conflicts(
            "route", layer="procedural", now=4.0
        )
        assert {item["value"] for item in remaining_conflicts} == {
            "north",
            "south",
        }
        store.invalidate(second.record_id, "conflicting old route")
        assert store.conflicts("route", layer="procedural", now=4.0) == []


def test_forget_removes_expired_and_low_trust_records(tmp_path):
    with SQLiteMemoryStore(tmp_path / "memory.sqlite3") as store:
        store.add(
            layer="episodic",
            key="event",
            value="current",
            source="docs/current.json",
            trust=0.9,
            observed_at=1.0,
        )
        store.add(
            layer="semantic",
            key="fact",
            value="expired",
            source="archive.json",
            trust=1.0,
            observed_at=1.0,
            expires_at=2.0,
        )
        store.add(
            layer="procedural",
            key="route",
            value="poison",
            source="note.txt",
            trust=0.1,
            observed_at=1.0,
        )
        forgotten = store.forget(now=3.0, min_trust=0.5)
        assert forgotten["forgotten"] == 2
        audit = store.audit(now=3.0, min_trust=0.5)
        assert sum(audit["active_counts"].values()) == 1
        assert audit["integrity_check"] == "ok"


def test_export_import_roundtrip_preserves_active_state(tmp_path):
    with SQLiteMemoryStore(tmp_path / "source.sqlite3") as source:
        source.add(
            layer="episodic",
            key="event",
            value="observed",
            source="trace.json",
            trust=0.9,
            observed_at=1.0,
        )
        source.add(
            layer="semantic",
            key="fact",
            value="verified",
            source="docs/spec.md",
            trust=0.95,
            observed_at=2.0,
        )
        payload = source.export_payload()

    with SQLiteMemoryStore(tmp_path / "target.sqlite3") as target:
        assert target.import_payload(payload) == 2
        assert target.best("event", layer="episodic", now=3.0).value == "observed"
        assert target.best("fact", layer="semantic", now=3.0).value == "verified"
        assert target.audit(now=3.0)["integrity_check"] == "ok"


def test_store_rejects_unknown_superseded_record(tmp_path):
    with SQLiteMemoryStore(tmp_path / "memory.sqlite3") as store:
        try:
            store.add(
                layer=MemoryLayer.SEMANTIC,
                key="route",
                value="new",
                source="docs/current.json",
                trust=0.9,
                observed_at=1.0,
                supersedes="missing",
            )
        except KeyError as exc:
            assert "missing" in str(exc)
        else:
            raise AssertionError("unknown supersession must fail")
        assert store.audit(now=1.0)["records"] == 0


def test_persistent_memory_probe_reports_expected_controls():
    result = run_persistent_memory_probe(episodes=8)
    assert result["status"] == "harness-validation"
    assert result["scientific_result"] is False
    assert result["metrics"]["records_before_forget"] == 40
    assert result["metrics"]["conflict_detection_rate"] == 1.0
    assert result["metrics"]["poison_or_stale_selection_rate"] == 0.0
    assert result["metrics"]["reopened_retrieval_correct_rate"] == 1.0
    assert result["metrics"]["rollback_atomic"] is True
    assert result["metrics"]["import_export_records_equal"] is True
    assert result["metrics"]["forgotten_records"] == 16
    assert result["metrics"]["active_records_after_forget"] == 16
    assert result["metrics"]["integrity_check"] == "ok"
    assert run_persistent_memory_probe(episodes=8) == result
