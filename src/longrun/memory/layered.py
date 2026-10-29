from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from statistics import fmean


class MemoryLayer(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass(frozen=True, slots=True)
class LayeredEntry:
    record_id: str
    layer: MemoryLayer
    key: str
    value: str
    source: str
    trust: float
    observed_at: float
    expires_at: float | None = None
    supersedes: str | None = None
    validated_by: tuple[str, ...] = ()


class LayeredMemory:
    """Three-layer memory with provenance, resolution, and active forgetting."""

    def __init__(self) -> None:
        self.records: list[LayeredEntry] = []
        self._counter = 0
        self._invalidated: dict[str, str] = {}

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
        try:
            resolved_layer = MemoryLayer(layer)
        except ValueError as exc:
            raise ValueError(f"unknown memory layer: {layer!r}") from exc
        if not key or not value or not source:
            raise ValueError("key, value, and source must be non-empty")
        if not 0.0 <= trust <= 1.0:
            raise ValueError("trust must be in [0, 1]")
        if expires_at is not None and expires_at < observed_at:
            raise ValueError("expires_at must not precede observed_at")
        if supersedes is not None and not any(
            record.record_id == supersedes for record in self.records
        ):
            raise KeyError(f"unknown superseded record: {supersedes}")
        self._counter += 1
        record = LayeredEntry(
            record_id=f"layered-{self._counter:06d}",
            layer=resolved_layer,
            key=key,
            value=value,
            source=source,
            trust=float(trust),
            observed_at=float(observed_at),
            expires_at=expires_at,
            supersedes=supersedes,
        )
        self.records.append(record)
        if supersedes:
            self._invalidated[supersedes] = f"superseded by {record.record_id}"
        return record

    def invalidate(self, record_id: str, reason: str) -> None:
        if not any(record.record_id == record_id for record in self.records):
            raise KeyError(f"unknown record: {record_id}")
        self._invalidated[record_id] = reason

    def validate(self, record_id: str, task_id: str) -> LayeredEntry:
        for index, record in enumerate(self.records):
            if record.record_id == record_id:
                updated = replace(
                    record,
                    validated_by=tuple([*record.validated_by, task_id]),
                )
                self.records[index] = updated
                return updated
        raise KeyError(f"unknown record: {record_id}")

    def _active(
        self,
        *,
        now: float,
        min_trust: float,
        layer: MemoryLayer | None = None,
        key: str | None = None,
    ) -> list[LayeredEntry]:
        return [
            record
            for record in self.records
            if record.record_id not in self._invalidated
            and record.trust >= min_trust
            and (record.expires_at is None or record.expires_at >= now)
            and (layer is None or record.layer == layer)
            and (key is None or record.key == key)
        ]

    def query(
        self,
        key: str,
        *,
        layer: MemoryLayer | str | None = None,
        now: float,
        min_trust: float = 0.5,
    ) -> list[LayeredEntry]:
        resolved_layer = MemoryLayer(layer) if layer is not None else None
        return sorted(
            self._active(
                now=now,
                min_trust=min_trust,
                layer=resolved_layer,
                key=key,
            ),
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
        forgotten = []
        for record in list(self.records):
            if record.record_id in self._invalidated:
                continue
            if (
                record.trust < min_trust
                or (record.expires_at is not None and record.expires_at < now)
            ):
                self._invalidated[record.record_id] = "forgotten: expired or low trust"
                forgotten.append(record.record_id)
        return {
            "forgotten": len(forgotten),
            "record_ids": forgotten,
        }

    def audit(self, *, now: float, min_trust: float = 0.5) -> dict:
        expired = []
        low_trust = []
        for record in self.records:
            if record.expires_at is not None and record.expires_at < now:
                expired.append(record.record_id)
            if record.trust < min_trust:
                low_trust.append(record.record_id)
        conflicts = []
        keys = sorted({(record.layer, record.key) for record in self.records})
        for layer, key in keys:
            conflicts.extend(
                self.conflicts(key, layer=layer, now=now, min_trust=min_trust)
            )
        active_counts = {
            layer.value: len(
                self._active(now=now, min_trust=min_trust, layer=layer)
            )
            for layer in MemoryLayer
        }
        return {
            "records": len(self.records),
            "active_counts": active_counts,
            "expired": expired,
            "low_trust": low_trust,
            "invalidated": dict(self._invalidated),
            "conflicts": conflicts,
        }


def run_layered_memory_probe(
    *,
    seed: int = 20261028,
    episodes: int = 100,
) -> dict:
    """Compare flat recency retrieval with layered provenance retrieval."""
    if episodes < 1:
        raise ValueError("episodes must be positive")
    flat_correct = 0
    flat_poison = 0
    layered_correct = 0
    layered_poison = 0
    conflict_cases = 0
    flat_layer_rows: dict[str, dict[str, int]] = {
        layer.value: {"correct": 0, "poison": 0, "total": 0}
        for layer in MemoryLayer
    }
    layered_layer_rows: dict[str, dict[str, int]] = {
        layer.value: {"correct": 0, "poison": 0, "total": 0}
        for layer in MemoryLayer
    }
    for episode in range(episodes):
        memory = LayeredMemory()
        correct_values = {
            "episodic": f"event-{episode}",
            "semantic": f"fact-{episode}",
            "procedural": f"procedure-{episode}",
        }
        for layer, correct in correct_values.items():
            memory.add(
                layer=layer,
                key="current",
                value=correct,
                source="docs/current.json",
                trust=0.95,
                observed_at=1.0,
            )
            memory.add(
                layer=layer,
                key="current",
                value=f"poison-{episode}",
                source="ambient-note.txt",
                trust=0.10,
                observed_at=2.0,
            )
            if episode % 3 == 0:
                memory.add(
                    layer=layer,
                    key="current",
                    value=f"expired-{episode}",
                    source="archive.json",
                    trust=1.0,
                    observed_at=3.0,
                    expires_at=4.0,
                )
            current = memory.best("current", layer=layer, now=5.0)
            flat = memory.records[-1]
            is_correct = current is not None and current.value == correct
            is_poison = flat.value != correct
            layered_correct += int(is_correct)
            layered_poison += int(current is None or current.value != correct)
            flat_correct += int(flat.value == correct)
            flat_poison += int(is_poison)
            flat_layer_rows[layer]["correct"] += int(flat.value == correct)
            flat_layer_rows[layer]["poison"] += int(is_poison)
            flat_layer_rows[layer]["total"] += 1
            layered_layer_rows[layer]["correct"] += int(is_correct)
            layered_layer_rows[layer]["poison"] += int(
                current is None or current.value != correct
            )
            layered_layer_rows[layer]["total"] += 1
        if episode % 3 == 0:
            conflict_cases += 1
        memory.forget(now=6.0, min_trust=0.5)
    total_records = sum(row["total"] for row in flat_layer_rows.values())
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "config": {"seed": seed, "episodes": episodes, "layers": len(MemoryLayer)},
        "conflict_cases": conflict_cases,
        "policies": {
            "flat-rag": {
                "correct_rate": flat_correct / total_records,
                "poison_rate": flat_poison / total_records,
                "by_layer": flat_layer_rows,
            },
            "layered-provenance": {
                "correct_rate": layered_correct / total_records,
                "final_correct_rate": (
                    1.0
                    if layered_poison == 0
                    else 1.0 - layered_poison / total_records
                ),
                "poison_rate": layered_poison / total_records,
                "by_layer": layered_layer_rows,
            },
        },
        "notes": [
            "This is a synthetic cross-session probe, not LongMemEval or LoCoMo.",
            "The flat-rag policy intentionally ignores trust, expiry, and layer provenance.",
        ],
    }
