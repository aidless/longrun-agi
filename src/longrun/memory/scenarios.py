from __future__ import annotations

from dataclasses import dataclass

from .provenance import MemoryRecord, NaiveMemory, ProvenanceMemory


@dataclass(frozen=True, slots=True)
class MemoryEvent:
    value: str
    source: str
    trust: float
    observed_at: float
    expires_at: float | None = None


@dataclass(frozen=True, slots=True)
class MemoryScenario:
    key: str
    expected: str
    events: tuple[MemoryEvent, ...]


def build_scenarios(count: int = 24) -> list[MemoryScenario]:
    if count < 1:
        raise ValueError("count must be positive")
    scenarios: list[MemoryScenario] = []
    for index in range(count):
        key = f"routing-rule-{index:03d}"
        expected = f"rule-current-{index:03d}"
        scenarios.append(
            MemoryScenario(
                key=key,
                expected=expected,
                events=(
                    MemoryEvent(
                        value=f"rule-old-{index:03d}",
                        source="archive/spec-v1.md",
                        trust=0.80,
                        observed_at=1.0,
                    ),
                    MemoryEvent(
                        value=f"rule-stale-{index:03d}",
                        source="archive/spec-v2.md",
                        trust=0.90,
                        observed_at=2.0,
                    ),
                    MemoryEvent(
                        value=f"rule-expired-{index:03d}",
                        source="archive/spec-v3.md",
                        trust=1.00,
                        observed_at=3.0,
                        expires_at=4.0,
                    ),
                    MemoryEvent(
                        value=expected,
                        source="docs/SPEC.md",
                        trust=0.95,
                        observed_at=4.0,
                    ),
                    MemoryEvent(
                        value=f"rule-poison-{index:03d}",
                        source="user-note.txt",
                        trust=0.10,
                        observed_at=5.0,
                    ),
                ),
            )
        )
    return scenarios


def _load_naive(scenario: MemoryScenario) -> MemoryRecord | None:
    memory = NaiveMemory()
    for event in scenario.events:
        memory.add(
            key=scenario.key,
            value=event.value,
            source=event.source,
            trust=event.trust,
            observed_at=event.observed_at,
            expires_at=event.expires_at,
        )
    return memory.best(scenario.key)


def _load_provenance(scenario: MemoryScenario) -> MemoryRecord | None:
    memory = ProvenanceMemory()
    for event in scenario.events:
        memory.add(
            key=scenario.key,
            value=event.value,
            source=event.source,
            trust=event.trust,
            observed_at=event.observed_at,
            expires_at=event.expires_at,
        )
    return memory.best(scenario.key, now=10.0, min_trust=0.5)


def _classify(selected: MemoryRecord | None, expected: str) -> str:
    if selected is None:
        return "missing"
    if selected.value == expected:
        return "correct"
    if "poison" in selected.value:
        return "poison"
    if "stale" in selected.value:
        return "stale"
    if "expired" in selected.value:
        return "expired"
    return "other_wrong"


def evaluate_memory_scenarios(count: int = 24) -> dict:
    scenarios = build_scenarios(count)
    policies = {
        "recency-only": _load_naive,
        "provenance-aware": _load_provenance,
    }
    output: dict = {"scenarios": count, "policies": {}}
    for name, loader in policies.items():
        counts: dict[str, int] = {}
        rows: list[dict] = []
        for scenario in scenarios:
            selected = loader(scenario)
            classification = _classify(selected, scenario.expected)
            counts[classification] = counts.get(classification, 0) + 1
            rows.append(
                {
                    "key": scenario.key,
                    "expected": scenario.expected,
                    "selected": selected.value if selected else None,
                    "selected_source": selected.source if selected else None,
                    "selected_trust": selected.trust if selected else None,
                    "classification": classification,
                }
            )
        output["policies"][name] = {
            "counts": counts,
            "correct_rate": counts.get("correct", 0) / len(scenarios),
            "poison_rate": counts.get("poison", 0) / len(scenarios),
            "stale_rate": counts.get("stale", 0) / len(scenarios),
            "rows": rows,
        }
    return output
