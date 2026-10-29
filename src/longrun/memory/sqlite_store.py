"""Durable SQLite implementation of layered provenance memory."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .layered import LayeredEntry, MemoryLayer


SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class MemoryMutation:
    layer: MemoryLayer | str
    key: str
    value: str
    source: str
    trust: float
    observed_at: float
    expires_at: float | None = None
    supersedes: str | None = None


class SQLiteMemoryStore:
    """Persistent layered memory with explicit transactions and audit output."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._migrate()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SQLiteMemoryStore":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            yield
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def _migrate(self) -> None:
        with self._transaction():
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    name TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_records (
                    record_id TEXT PRIMARY KEY,
                    layer TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    source TEXT NOT NULL,
                    trust REAL NOT NULL,
                    observed_at REAL NOT NULL,
                    expires_at REAL,
                    supersedes TEXT,
                    validated_by TEXT NOT NULL DEFAULT '[]',
                    invalidated_reason TEXT,
                    created_order INTEGER NOT NULL UNIQUE,
                    FOREIGN KEY (supersedes) REFERENCES memory_records(record_id)
                );
                CREATE INDEX IF NOT EXISTS memory_lookup
                    ON memory_records(layer, key, invalidated_reason);
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id INTEGER PRIMARY KEY,
                    action TEXT NOT NULL,
                    record_id TEXT,
                    detail TEXT NOT NULL
                );
                """
            )
            self._connection.execute(
                "INSERT OR IGNORE INTO metadata(name, value) VALUES(?, ?)",
                ("schema_version", str(SCHEMA_VERSION)),
            )

    @staticmethod
    def _validate_mutation(mutation: MemoryMutation) -> MemoryLayer:
        try:
            layer = MemoryLayer(mutation.layer)
        except ValueError as exc:
            raise ValueError(
                f"unknown memory layer: {mutation.layer!r}"
            ) from exc
        if not mutation.key or not mutation.value or not mutation.source:
            raise ValueError("key, value, and source must be non-empty")
        if not 0.0 <= mutation.trust <= 1.0:
            raise ValueError("trust must be in [0, 1]")
        if (
            mutation.expires_at is not None
            and mutation.expires_at < mutation.observed_at
        ):
            raise ValueError("expires_at must not precede observed_at")
        return layer

    def _log(self, action: str, record_id: str | None, detail: dict) -> None:
        self._connection.execute(
            "INSERT INTO audit_events(action, record_id, detail) VALUES(?, ?, ?)",
            (
                action,
                record_id,
                json.dumps(detail, sort_keys=True, separators=(",", ":")),
            ),
        )

    def _add_in_transaction(self, mutation: MemoryMutation) -> LayeredEntry:
        layer = self._validate_mutation(mutation)
        if mutation.supersedes is not None:
            row = self._connection.execute(
                """
                SELECT invalidated_reason
                FROM memory_records
                WHERE record_id = ?
                """,
                (mutation.supersedes,),
            ).fetchone()
            if row is None:
                raise KeyError(f"unknown superseded record: {mutation.supersedes}")
            if row["invalidated_reason"] is not None:
                raise ValueError(
                    f"superseded record is inactive: {mutation.supersedes}"
                )
        next_order = self._connection.execute(
            "SELECT COALESCE(MAX(created_order), 0) + 1 AS next_order FROM memory_records"
        ).fetchone()["next_order"]
        record_id = f"persistent-{next_order:06d}"
        self._connection.execute(
            """
            INSERT INTO memory_records(
                record_id, layer, key, value, source, trust, observed_at,
                expires_at, supersedes, validated_by, invalidated_reason,
                created_order
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, '[]', NULL, ?)
            """,
            (
                record_id,
                layer.value,
                mutation.key,
                mutation.value,
                mutation.source,
                float(mutation.trust),
                float(mutation.observed_at),
                mutation.expires_at,
                mutation.supersedes,
                next_order,
            ),
        )
        self._log("add", record_id, {"key": mutation.key, "layer": layer.value})
        if mutation.supersedes is not None:
            self._connection.execute(
                """
                UPDATE memory_records
                SET invalidated_reason = ?
                WHERE record_id = ?
                """,
                (f"superseded by {record_id}", mutation.supersedes),
            )
            self._log(
                "supersede",
                mutation.supersedes,
                {"replacement": record_id},
            )
        return LayeredEntry(
            record_id=record_id,
            layer=layer,
            key=mutation.key,
            value=mutation.value,
            source=mutation.source,
            trust=float(mutation.trust),
            observed_at=float(mutation.observed_at),
            expires_at=mutation.expires_at,
            supersedes=mutation.supersedes,
        )

    def add(
        self,
        *,
        layer: MemoryLayer | str,
        key: str,
        value: str,
        source: str,
        trust: float,
        observed_at: float,
        expires_at: float | None = None,
        supersedes: str | None = None,
    ) -> LayeredEntry:
        mutation = MemoryMutation(
            layer=layer,
            key=key,
            value=value,
            source=source,
            trust=trust,
            observed_at=observed_at,
            expires_at=expires_at,
            supersedes=supersedes,
        )
        with self._transaction():
            return self._add_in_transaction(mutation)

    def apply_batch(self, mutations: list[MemoryMutation]) -> list[LayeredEntry]:
        """Apply a batch atomically; any invalid mutation rolls back all writes."""
        with self._transaction():
            return [
                self._add_in_transaction(mutation) for mutation in mutations
            ]

    def invalidate(self, record_id: str, reason: str) -> None:
        if not reason.strip():
            raise ValueError("reason must be non-empty")
        with self._transaction():
            cursor = self._connection.execute(
                """
                UPDATE memory_records
                SET invalidated_reason = ?
                WHERE record_id = ? AND invalidated_reason IS NULL
                """,
                (reason, record_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"unknown or inactive record: {record_id}")
            self._log("invalidate", record_id, {"reason": reason})

    def validate(self, record_id: str, task_id: str) -> LayeredEntry:
        if not task_id.strip():
            raise ValueError("task_id must be non-empty")
        with self._transaction():
            row = self._connection.execute(
                "SELECT * FROM memory_records WHERE record_id = ?",
                (record_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"unknown record: {record_id}")
            validated_by = json.loads(row["validated_by"])
            if task_id not in validated_by:
                validated_by.append(task_id)
            self._connection.execute(
                "UPDATE memory_records SET validated_by = ? WHERE record_id = ?",
                (
                    json.dumps(validated_by, sort_keys=True),
                    record_id,
                ),
            )
            self._log("validate", record_id, {"task_id": task_id})
            return self._row_to_entry(
                self._connection.execute(
                    "SELECT * FROM memory_records WHERE record_id = ?",
                    (record_id,),
                ).fetchone()
            )

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> LayeredEntry:
        return LayeredEntry(
            record_id=row["record_id"],
            layer=MemoryLayer(row["layer"]),
            key=row["key"],
            value=row["value"],
            source=row["source"],
            trust=row["trust"],
            observed_at=row["observed_at"],
            expires_at=row["expires_at"],
            supersedes=row["supersedes"],
            validated_by=tuple(json.loads(row["validated_by"])),
        )

    def query(
        self,
        key: str,
        *,
        layer: MemoryLayer | str | None = None,
        now: float,
        min_trust: float = 0.5,
    ) -> list[LayeredEntry]:
        conditions = [
            "key = ?",
            "invalidated_reason IS NULL",
            "trust >= ?",
            "(expires_at IS NULL OR expires_at >= ?)",
        ]
        parameters: list[object] = [key, min_trust, now]
        if layer is not None:
            conditions.append("layer = ?")
            parameters.append(MemoryLayer(layer).value)
        rows = self._connection.execute(
            "SELECT * FROM memory_records WHERE "
            + " AND ".join(conditions),
            parameters,
        ).fetchall()
        entries = [self._row_to_entry(row) for row in rows]
        return sorted(
            entries,
            key=lambda record: (
                bool(record.validated_by),
                record.trust,
                record.observed_at,
                record.record_id,
            ),
            reverse=True,
        )

    def best(
        self,
        key: str,
        *,
        layer: MemoryLayer | str,
        now: float,
        min_trust: float = 0.5,
    ) -> LayeredEntry | None:
        matches = self.query(
            key,
            layer=layer,
            now=now,
            min_trust=min_trust,
        )
        return matches[0] if matches else None

    def conflicts(
        self,
        key: str,
        *,
        layer: MemoryLayer | str,
        now: float,
        min_trust: float = 0.5,
    ) -> list[dict]:
        active = self.query(
            key,
            layer=layer,
            now=now,
            min_trust=min_trust,
        )
        by_value: dict[str, list[str]] = {}
        for record in active:
            by_value.setdefault(record.value, []).append(record.record_id)
        if len(by_value) <= 1:
            return []
        return [
            {
                "key": key,
                "layer": MemoryLayer(layer).value,
                "value": value,
                "record_ids": ids,
            }
            for value, ids in sorted(by_value.items())
        ]

    def forget(self, *, now: float, min_trust: float = 0.5) -> dict:
        active = self._connection.execute(
            "SELECT * FROM memory_records WHERE invalidated_reason IS NULL"
        ).fetchall()
        forgotten: list[str] = []
        with self._transaction():
            for row in active:
                reason = None
                if row["trust"] < min_trust:
                    reason = "forgotten: low trust"
                elif row["expires_at"] is not None and row["expires_at"] < now:
                    reason = "forgotten: expired"
                if reason is None:
                    continue
                self._connection.execute(
                    """
                    UPDATE memory_records
                    SET invalidated_reason = ?
                    WHERE record_id = ?
                    """,
                    (reason, row["record_id"]),
                )
                self._log(
                    "forget",
                    row["record_id"],
                    {"reason": reason, "now": now},
                )
                forgotten.append(row["record_id"])
        return {"forgotten": len(forgotten), "record_ids": forgotten}

    def audit(self, *, now: float, min_trust: float = 0.5) -> dict:
        rows = self._connection.execute(
            "SELECT * FROM memory_records ORDER BY created_order"
        ).fetchall()
        invalidated = {
            row["record_id"]: row["invalidated_reason"]
            for row in rows
            if row["invalidated_reason"] is not None
        }
        expired = [
            row["record_id"]
            for row in rows
            if row["invalidated_reason"] is None
            and row["expires_at"] is not None
            and row["expires_at"] < now
        ]
        low_trust = [
            row["record_id"]
            for row in rows
            if row["invalidated_reason"] is None and row["trust"] < min_trust
        ]
        conflicts: list[dict] = []
        keys = sorted({(row["layer"], row["key"]) for row in rows})
        for layer, key in keys:
            conflicts.extend(
                self.conflicts(
                    key,
                    layer=layer,
                    now=now,
                    min_trust=min_trust,
                )
            )
        active_counts = {
            layer.value: len(
                self.query(
                    "__all__",
                    layer=layer,
                    now=now,
                    min_trust=min_trust,
                )
            )
            for layer in MemoryLayer
        }
        # query() requires one key, so count active records directly.
        active_counts = {}
        for layer in MemoryLayer:
            active_counts[layer.value] = self._connection.execute(
                """
                SELECT COUNT(*)
                FROM memory_records
                WHERE layer = ?
                  AND invalidated_reason IS NULL
                  AND trust >= ?
                  AND (expires_at IS NULL OR expires_at >= ?)
                """,
                (layer.value, min_trust, now),
            ).fetchone()[0]
        integrity = self._connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
        schema_version = int(
            self._connection.execute(
                "SELECT value FROM metadata WHERE name = 'schema_version'"
            ).fetchone()[0]
        )
        return {
            "records": len(rows),
            "active_counts": active_counts,
            "expired": expired,
            "low_trust": low_trust,
            "invalidated": invalidated,
            "conflicts": conflicts,
            "integrity_check": integrity,
            "schema_version": schema_version,
        }

    def export_payload(self) -> dict:
        rows = self._connection.execute(
            "SELECT * FROM memory_records ORDER BY created_order"
        ).fetchall()
        return {
            "schema_version": SCHEMA_VERSION,
            "records": [
                {
                    "record_id": row["record_id"],
                    "layer": row["layer"],
                    "key": row["key"],
                    "value": row["value"],
                    "source": row["source"],
                    "trust": row["trust"],
                    "observed_at": row["observed_at"],
                    "expires_at": row["expires_at"],
                    "supersedes": row["supersedes"],
                    "validated_by": json.loads(row["validated_by"]),
                    "invalidated_reason": row["invalidated_reason"],
                    "created_order": row["created_order"],
                }
                for row in rows
            ],
        }

    def import_payload(self, payload: dict) -> int:
        if self._connection.execute(
            "SELECT COUNT(*)"
            " FROM memory_records"
        ).fetchone()[0]:
            raise ValueError("import requires an empty store")
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported schema version")
        records = sorted(
            payload.get("records", []),
            key=lambda record: record["created_order"],
        )
        with self._transaction():
            for record in records:
                MemoryLayer(record["layer"])
                if not record["record_id"] or not record["key"]:
                    raise ValueError("record id and key must be non-empty")
                if not 0.0 <= record["trust"] <= 1.0:
                    raise ValueError("trust must be in [0, 1]")
                self._connection.execute(
                    """
                    INSERT INTO memory_records(
                        record_id, layer, key, value, source, trust,
                        observed_at, expires_at, supersedes, validated_by,
                        invalidated_reason, created_order
                    ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record["record_id"],
                        record["layer"],
                        record["key"],
                        record["value"],
                        record["source"],
                        float(record["trust"]),
                        float(record["observed_at"]),
                        record["expires_at"],
                        record["supersedes"],
                        json.dumps(record["validated_by"], sort_keys=True),
                        record["invalidated_reason"],
                        int(record["created_order"]),
                    ),
                )
                self._log(
                    "import",
                    record["record_id"],
                    {"key": record["key"], "layer": record["layer"]},
                )
        return len(records)


def run_persistent_memory_probe(*, episodes: int = 32) -> dict:
    if episodes < 1:
        raise ValueError("episodes must be positive")
    with tempfile.TemporaryDirectory(prefix="longrun-memory-") as directory:
        database = Path(directory) / "memory.sqlite3"
        imported_database = Path(directory) / "imported.sqlite3"
        conflict_hits = 0
        poison_hits = 0
        with SQLiteMemoryStore(database) as store:
            for index in range(episodes):
                layer = tuple(MemoryLayer)[index % len(MemoryLayer)]
                key = f"route-{index:03d}"
                safe = store.add(
                    layer=layer,
                    key=key,
                    value=f"safe-{index:03d}",
                    source="docs/current.json",
                    trust=0.95,
                    observed_at=1.0,
                )
                store.add(
                    layer=layer,
                    key=key,
                    value=f"poison-{index:03d}",
                    source="ambient-note.txt",
                    trust=0.10,
                    observed_at=2.0,
                )
                store.add(
                    layer=layer,
                    key=key,
                    value=f"expired-{index:03d}",
                    source="archive.json",
                    trust=1.0,
                    observed_at=3.0,
                    expires_at=4.0,
                )
                old = store.add(
                    layer=layer,
                    key=key,
                    value=f"old-{index:03d}",
                    source="archive/old.md",
                    trust=0.90,
                    observed_at=1.0,
                )
                conflict_hits += int(
                    bool(store.conflicts(key, layer=layer, now=5.0))
                )
                store.add(
                    layer=layer,
                    key=key,
                    value=safe.value,
                    source="docs/current.json",
                    trust=0.95,
                    observed_at=4.0,
                    supersedes=old.record_id,
                )
                selected = store.best(key, layer=layer, now=5.0)
                poison_hits += int(
                    selected is None or selected.value != safe.value
                )
            before_rollback = store.audit(now=5.0)["records"]
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
            except ValueError:
                pass
            after_rollback = store.audit(now=5.0)["records"]
            before_forget = store.audit(now=5.0)
            exported = store.export_payload()

        with SQLiteMemoryStore(database) as reopened:
            reopened_correct = sum(
                (
                    selected := reopened.best(
                        f"route-{index:03d}",
                        layer=tuple(MemoryLayer)[index % len(MemoryLayer)],
                        now=5.0,
                    )
                )
                is not None
                and selected.value == f"safe-{index:03d}"
                for index in range(episodes)
            )
            forgotten = reopened.forget(now=5.0, min_trust=0.5)
            after_forget = reopened.audit(now=5.0, min_trust=0.5)

        with SQLiteMemoryStore(imported_database) as imported:
            imported_count = imported.import_payload(exported)
            imported_audit = imported.audit(now=5.0)

        return {
            "status": "harness-validation",
            "scientific_result": False,
            "config": {
                "episodes": episodes,
                "layers": len(MemoryLayer),
                "schema_version": SCHEMA_VERSION,
            },
            "metrics": {
                "records_before_forget": before_forget["records"],
                "conflict_detection_rate": conflict_hits / episodes,
                "poison_or_stale_selection_rate": poison_hits / episodes,
                "reopened_retrieval_correct_rate": reopened_correct / episodes,
                "rollback_atomic": before_rollback == after_rollback,
                "exported_records": len(exported["records"]),
                "imported_records": imported_count,
                "import_export_records_equal": (
                    len(exported["records"]) == imported_count
                ),
                "forgotten_records": forgotten["forgotten"],
                "active_records_after_forget": sum(
                    after_forget["active_counts"].values()
                ),
                "integrity_check": imported_audit["integrity_check"],
            },
            "notes": [
                "The store uses standard-library SQLite only.",
                "Restart, rollback, conflict, expiry, and import/export checks are synthetic.",
                "This is a persistence-engineering control, not LongMemEval or LoCoMo.",
            ],
        }
