from __future__ import annotations

import random


def _goal_vocabulary() -> tuple[str, ...]:
    return (
        "archive",
        "review",
        "publish",
        "cleanup",
        "preserve",
        "summarize",
    )


def run_goal_drift_probe(
    *,
    seed: int = 20261028,
    episodes: int = 100,
    steps: int = 50,
) -> dict:
    """Measure whether ambient events pull a goal-following policy off task."""
    if episodes < 1 or steps < 1:
        raise ValueError("episodes and steps must be positive")
    rng = random.Random(seed)
    vocab = _goal_vocabulary()

    def run_policy(policy_name: str, episode: int) -> dict:
        true_goal = vocab[episode % len(vocab)]
        event_rng = random.Random(seed + episode * 1009)
        current = true_goal
        decay = 1.0
        correct = 0
        switches = 0
        history = []
        for step in range(steps):
            distractor = vocab[event_rng.randrange(len(vocab))]
            strength = event_rng.random()
            if policy_name == "pinned":
                current = true_goal
            elif policy_name == "recency":
                if step % 7 == 0:
                    current = distractor
                    switches += 1
            elif policy_name == "decay":
                decay *= 0.97
                current = true_goal if decay >= strength else distractor
            else:
                raise ValueError(f"unknown policy: {policy_name}")
            correct += int(current == true_goal)
            history.append(
                {
                    "step": step,
                    "distractor": distractor,
                    "distractor_strength": round(strength, 6),
                    "selected": current,
                    "correct": current == true_goal,
                }
            )
        return {
            "true_goal": true_goal,
            "accuracy": correct / steps,
            "final_accuracy": float(history[-1]["correct"]),
            "drift_rate": switches / steps,
            "history": history,
        }

    results = {}
    for policy in ("pinned", "recency", "decay"):
        rows = [run_policy(policy, episode) for episode in range(episodes)]
        results[policy] = {
            "episodes": episodes,
            "steps": steps,
            "accuracy": sum(row["accuracy"] for row in rows) / episodes,
            "final_accuracy": sum(row["final_accuracy"] for row in rows)
            / episodes,
            "drift_rate": sum(row["drift_rate"] for row in rows) / episodes,
            "correct_steps": sum(
                int(row["accuracy"] * steps) for row in rows
            ),
            "example_episode": rows[0],
        }
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "config": {
            "seed": seed,
            "episodes": episodes,
            "steps": steps,
            "goal_vocabulary": len(vocab),
        },
        "policies": results,
        "notes": [
            "Ambient distractors are synthetic events, not prompts to an LLM.",
            "The probe measures control behavior under explicit goal persistence.",
        ],
    }
