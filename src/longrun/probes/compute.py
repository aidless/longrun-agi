from __future__ import annotations

import random


def _jobs(seed: int, count: int) -> list[dict]:
    rng = random.Random(seed)
    jobs = []
    for index in range(count):
        cost = rng.randint(1, 12)
        value = rng.randint(1, 20)
        deadline = rng.randint(2, count + 4)
        jobs.append(
            {
                "job_id": f"job-{index:03d}",
                "cost": cost,
                "value": value,
                "deadline": deadline,
            }
        )
    return jobs


def _schedule(jobs: list[dict], policy: str, budget: int, seed: int) -> dict:
    rng = random.Random(seed)
    if policy == "fifo":
        ordered = list(jobs)
    elif policy == "shortest-job":
        ordered = sorted(jobs, key=lambda job: (job["cost"], job["deadline"]))
    elif policy == "value-density":
        ordered = sorted(
            jobs,
            key=lambda job: (-job["value"] / job["cost"], job["deadline"]),
        )
    elif policy == "safe-value-density":
        ordered = sorted(
            jobs,
            key=lambda job: (
                -job["value"] / job["cost"],
                job["deadline"],
                job["cost"],
            ),
        )
    elif policy == "random":
        ordered = list(jobs)
        rng.shuffle(ordered)
    else:
        raise ValueError(f"unknown policy: {policy}")

    spent = 0
    value = 0
    selected = []
    deadline_misses = 0
    completion = 0
    for job in ordered:
        if policy == "safe-value-density" and (
            completion + job["cost"] > job["deadline"]
        ):
            continue
        if completion + job["cost"] > job["deadline"]:
            deadline_misses += 1
        if spent + job["cost"] > budget:
            continue
        spent += job["cost"]
        value += job["value"]
        completion += job["cost"]
        selected.append(job["job_id"])
    return {
        "policy": policy,
        "spent": spent,
        "value": value,
        "deadline_misses": deadline_misses,
        "selected": selected,
        "overspend": spent > budget,
        "utilization": spent / budget if budget else 0.0,
    }


def run_compute_probe(
    *,
    seed: int = 20261028,
    jobs: int = 120,
    budget: int = 240,
) -> dict:
    """Compare deterministic CPU scheduling policies under a fixed budget."""
    if jobs < 1 or budget < 1:
        raise ValueError("jobs and budget must be positive")
    workload = _jobs(seed, jobs)
    policies = {}
    for policy in (
        "fifo",
        "shortest-job",
        "value-density",
        "safe-value-density",
        "random",
    ):
        policies[policy] = _schedule(workload, policy, budget, seed)
    robustness_seeds = 40
    frequency: dict[str, int] = {}
    value_density_wins = 0
    for offset in range(robustness_seeds):
        current_seed = seed + offset * 7919
        current_jobs = _jobs(current_seed, jobs)
        current_results = {
            policy: _schedule(current_jobs, policy, budget, current_seed)
            for policy in (
                "fifo",
                "shortest-job",
                "value-density",
                "safe-value-density",
                "random",
            )
        }
        best = max(
            current_results,
            key=lambda name: (
                current_results[name]["value"],
                -current_results[name]["deadline_misses"],
            ),
        )
        frequency[best] = frequency.get(best, 0) + 1
        value_density_wins += int(best == "value-density")
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "config": {
            "seed": seed,
            "jobs": jobs,
            "budget": budget,
            "cost_range": [1, 12],
            "value_range": [1, 20],
            "robustness_seeds": robustness_seeds,
        },
        "policies": policies,
        "best_policy_by_value": max(
            policies,
            key=lambda name: (policies[name]["value"], -policies[name]["spent"]),
        ),
        "robustness": {
            "seeds": robustness_seeds,
            "best_policy_frequency": dict(sorted(frequency.items())),
            "value_density_wins_share": value_density_wins / robustness_seeds,
            "note": (
                "Ties are broken by fewer deadline misses. This checks seed "
                "sensitivity of a synthetic scheduler, not real hardware."
            ),
        },
        "notes": [
            "This is a synthetic scheduling problem, not a claim about accelerator performance.",
            "No job is executed and no external resource is consumed.",
        ],
    }
