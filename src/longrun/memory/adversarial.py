from __future__ import annotations

from .provenance import NaiveMemory, ProvenanceMemory


def run_adversarial_memory_probe(
    *,
    seed: int = 20261028,
    episodes: int = 100,
) -> dict:
    """Compare recency-only and provenance-aware memory on mixed events."""
    if episodes < 1:
        raise ValueError("episodes must be positive")
    results = {
        "recency": {"correct": 0, "poisoned": 0, "poison_events": 0},
        "source-trust": {"correct": 0, "poisoned": 0, "poison_events": 0},
    }
    event_counts = {"expired": 0, "superseded": 0}
    for episode in range(episodes):
        if episode % 2 == 0:
            naive = NaiveMemory()
            provenance = ProvenanceMemory()
            naive.add(
                key="route",
                value="safe-route",
                source="docs/SPEC.md",
                trust=0.95,
                observed_at=1.0,
            )
            provenance.add(
                key="route",
                value="safe-route",
                source="docs/SPEC.md",
                trust=0.95,
                observed_at=1.0,
            )
            naive.add(
                key="route",
                value="unsafe-route",
                source="ambient-note.txt",
                trust=0.10,
                observed_at=2.0,
            )
            provenance.add(
                key="route",
                value="unsafe-route",
                source="ambient-note.txt",
                trust=0.10,
                observed_at=2.0,
            )
            naive_best = naive.best("route")
            provenance_best = provenance.best("route", now=2.0, min_trust=0.5)
            results["recency"]["poisoned"] += int(
                naive_best is not None and naive_best.value == "unsafe-route"
            )
            results["recency"]["poison_events"] += 1
            results["source-trust"]["poison_events"] += 1
            results["source-trust"]["poisoned"] += int(
                provenance_best is not None
                and provenance_best.value == "unsafe-route"
            )
            results["recency"]["correct"] += int(
                naive_best is not None and naive_best.value == "safe-route"
            )
            results["source-trust"]["correct"] += int(
                provenance_best is not None
                and provenance_best.value == "safe-route"
            )
            event_counts["superseded"] += 1
            if episode % 4 == 0:
                event_counts["expired"] += 1
        else:
            naive = NaiveMemory()
            provenance = ProvenanceMemory()
            naive.add(
                key="route",
                value="current-route",
                source="docs/SPEC.md",
                trust=0.95,
                observed_at=3.0,
            )
            old = provenance.add(
                key="route",
                value="old-route",
                source="docs/SPEC.md",
                trust=0.95,
                observed_at=1.0,
            )
            provenance.add(
                key="route",
                value="current-route",
                source="docs/SPEC.md",
                trust=0.95,
                observed_at=3.0,
                supersedes=old.record_id,
            )
            if episode % 3 == 0:
                naive.add(
                    key="route",
                    value="expired-route",
                    source="archive.md",
                    trust=1.0,
                    observed_at=4.0,
                    expires_at=5.0,
                )
                provenance.add(
                    key="route",
                    value="expired-route",
                    source="archive.md",
                    trust=1.0,
                    observed_at=4.0,
                    expires_at=5.0,
                )
                event_counts["expired"] += 1
            naive_best = naive.best("route")
            provenance_best = provenance.best("route", now=6.0, min_trust=0.5)
            results["recency"]["poisoned"] += int(
                naive_best is not None and "expired" in naive_best.value
            )
            if episode % 3 == 0:
                results["recency"]["poison_events"] += 1
                results["source-trust"]["poison_events"] += 1
            results["source-trust"]["poisoned"] += int(
                provenance_best is not None
                and "expired" in provenance_best.value
            )
            results["recency"]["correct"] += int(
                naive_best is not None and naive_best.value == "current-route"
            )
            results["source-trust"]["correct"] += int(
                provenance_best is not None
                and provenance_best.value == "current-route"
            )
            event_counts["superseded"] += 1
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "config": {"seed": seed, "episodes": episodes},
        "event_counts": event_counts,
        "policies": {
            name: {
                "correct": values["correct"],
                "poisoned": values["poisoned"],
                "poison_rate": values["poisoned"] / episodes,
                "stale_selection_rate": values["poisoned"] / episodes,
                "poison_event_rate": (
                    values["poisoned"] / values["poison_events"]
                    if values["poison_events"]
                    else 0.0
                ),
                "correct_rate": values["correct"] / episodes,
            }
            for name, values in results.items()
        },
        "notes": [
            "Events include low-trust ambient notes, stale sources, supersession, and expiry.",
            "The probe is synthetic and deterministic; it does not evaluate an LLM.",
        ],
    }
