from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    record_id: str
    key: str
    value: str
    source: str
    trust: float
    observed_at: float
    expires_at: float | None = None
    supersedes: str | None = None


class _MemoryBase:
    def __init__(self) -> None:
        self.records: list[MemoryRecord] = []
        self._counter = 0

    def add(
        self,
        *,
        key: str,
        value: str,
        source: str,
        trust: float,
        observed_at: float,
        expires_at: float | None = None,
        supersedes: str | None = None,
    ) -> MemoryRecord:
        if not key or not value or not source:
            raise ValueError("key, value, and source must be non-empty")
        if not 0.0 <= trust <= 1.0:
            raise ValueError("trust must be in [0, 1]")
        if expires_at is not None and expires_at < observed_at:
            raise ValueError("expires_at must not precede observed_at")
        self._counter += 1
        record = MemoryRecord(
            record_id=f"mem-{self._counter:06d}",
            key=key,
            value=value,
            source=source,
            trust=trust,
            observed_at=observed_at,
            expires_at=expires_at,
            supersedes=supersedes,
        )
        self.records.append(record)
        return record

    def for_key(self, key: str) -> list[MemoryRecord]:
        return [record for record in self.records if record.key == key]


class NaiveMemory(_MemoryBase):
    """Recency-only baseline used to test retrieval sensitivity."""

    def best(self, key: str) -> MemoryRecord | None:
        matches = self.for_key(key)
        return matches[-1] if matches else None


class ProvenanceMemory(_MemoryBase):
    """Memory that respects trust, expiry, invalidation, and supersession."""

    def __init__(self) -> None:
        super().__init__()
        self._invalidated: dict[str, str] = {}

    def add(
        self,
        *,
        key: str,
        value: str,
        source: str,
        trust: float,
        observed_at: float,
        expires_at: float | None = None,
        supersedes: str | None = None,
    ) -> MemoryRecord:
        record = super().add(
            key=key,
            value=value,
            source=source,
            trust=trust,
            observed_at=observed_at,
            expires_at=expires_at,
            supersedes=supersedes,
        )
        if supersedes:
            self.invalidate(supersedes, f"superseded by {record.record_id}")
        return record

    def invalidate(self, record_id: str, reason: str) -> None:
        if not any(record.record_id == record_id for record in self.records):
            raise KeyError(f"unknown record: {record_id}")
        self._invalidated[record_id] = reason

    def query(
        self,
        key: str,
        *,
        now: float,
        min_trust: float = 0.0,
    ) -> list[MemoryRecord]:
        return [
            record
            for record in self.for_key(key)
            if record.record_id not in self._invalidated
            and record.trust >= min_trust
            and (record.expires_at is None or record.expires_at >= now)
        ]

    def best(
        self,
        key: str,
        *,
        now: float,
        min_trust: float = 0.5,
    ) -> MemoryRecord | None:
        active = self.query(key, now=now, min_trust=min_trust)
        if not active:
            return None
        return max(active, key=lambda record: (record.observed_at, record.trust, record.record_id))

    def conflicts(
        self,
        key: str,
        *,
        now: float,
        min_trust: float = 0.0,
    ) -> list[dict]:
        active = self.query(key, now=now, min_trust=min_trust)
        by_value: dict[str, list[str]] = {}
        for record in active:
            by_value.setdefault(record.value, []).append(record.record_id)
        if len(by_value) <= 1:
            return []
        return [
            {"key": key, "value": value, "record_ids": record_ids}
            for value, record_ids in sorted(by_value.items())
        ]

    def audit(self, *, now: float, min_trust: float = 0.5) -> dict:
        expired: list[str] = []
        low_trust: list[str] = []
        invalidated: dict[str, str] = dict(self._invalidated)
        for record in self.records:
            if record.expires_at is not None and record.expires_at < now:
                expired.append(record.record_id)
            if record.trust < min_trust:
                low_trust.append(record.record_id)
        conflict_list: list[dict] = []
        for key in sorted({record.key for record in self.records}):
            conflict_list.extend(self.conflicts(key, now=now, min_trust=min_trust))
        return {
            "records": len(self.records),
            "active_records": sum(
                len(self.query(key, now=now, min_trust=min_trust))
                for key in {record.key for record in self.records}
            ),
            "expired": expired,
            "low_trust": low_trust,
            "invalidated": invalidated,
            "conflicts": conflict_list,
        }
