from __future__ import annotations

from datetime import datetime, timezone

from .agent_loop import run_agent_loop_audit
from .analysis.factorial import run_estimator_grid
from .benchmarks.clear_v1 import (
    build_split_manifest,
    generate_clear_v1_tasks,
    run_scripted_baselines,
)
from .clear.cross_family import run_cross_family_probe
from .clear.generators import (
    generate_factorial_tasks,
    generate_fault_tasks,
    generate_tasks,
    generate_three_factor_tasks,
)
from .clear.failure_matrix import run_failure_matrix
from .clear.recovery import run_recovery_matrix
from .clear.policies import (
    ConfigurableSpecPolicy,
    MemorySpecPolicy,
    ReactiveSpecPolicy,
    StickySpecPolicy,
)
from .clear.runner import evaluate
from .clear.second_generator import generate_second_factorial_tasks
from .controls.claim_gate import run_claim_schema_probe
from .controls.confounding import run_confounding_control_probe
from .controls.evidence import EvidenceGate, audit_control_suite
from .controls.research_agent import run_research_agent_probe
from .evaluation.protocol import run_model_protocol_dry_run
from .memory.scenarios import evaluate_memory_scenarios
from .memory.adversarial import run_adversarial_memory_probe
from .memory.layered import run_layered_memory_probe
from .memory.sqlite_store import run_persistent_memory_probe
from .probes.compute import run_compute_probe
from .probes.adaptive_controller import run_adaptive_controller_probe
from .probes.goal_drift import run_goal_drift_probe
from .probes.goal_drift_monitor import run_goal_drift_monitor_probe
from .probes.verifier_gap import run_verifier_gap_probe
from .probes.verifier_rewards import run_verifier_reward_probe
from .probes.world_model import run_world_model_probe
from .probes.world_model_calibration import run_world_model_calibration_probe
from .runtime.real_faults import run_real_fault_matrix


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _p7_summary(quick: bool) -> dict:
    instances = 1 if quick else 4
    clear_tasks = generate_tasks(instances_per_variant=instances)
    reactive = evaluate(clear_tasks, ReactiveSpecPolicy, "reactive-spec")
    sticky = evaluate(clear_tasks, StickySpecPolicy, "sticky-spec")
    factorial_tasks = generate_factorial_tasks(instances_per_variant=instances)
    robust = evaluate(
        factorial_tasks,
        lambda: ConfigurableSpecPolicy(retain_rule=False, retry_on_error=True),
        "spec-recheck",
    )
    three_factor_tasks = generate_three_factor_tasks(
        instances_per_variant=instances
    )
    provenance = evaluate(
        three_factor_tasks,
        lambda: MemorySpecPolicy(trusted_memory=True),
        "memory-provenance",
    )
    cross_family = run_cross_family_probe(seed=20261028)
    clear_v1_tasks = generate_clear_v1_tasks(seed=20261028)
    clear_v1_manifest = build_split_manifest(clear_v1_tasks, seed=20261028)
    clear_v1_baselines = run_scripted_baselines(clear_v1_tasks)
    second_tasks = generate_second_factorial_tasks(
        instances_per_variant=1 if quick else 2,
        seed=20261028,
    )
    second_reactive = evaluate(
        second_tasks,
        lambda: ConfigurableSpecPolicy(
            retain_rule=False,
            retry_on_error=True,
            source_dir="queue",
        ),
        "second-recheck",
    )
    model_protocol = run_model_protocol_dry_run()
    return {
        "status": "implemented-v2",
        "clear_tasks": len(clear_tasks),
        "reactive_shift_success": reactive["overall"]["shift_success_rate"],
        "sticky_shift_success": sticky["overall"]["shift_success_rate"],
        "factorial_tasks": len(factorial_tasks),
        "factorial_recheck_success": robust["overall"]["success_rate"],
        "three_factor_tasks": len(three_factor_tasks),
        "three_factor_provenance_success": provenance["overall"]["success_rate"],
        "cross_family_transfer": cross_family["directions"],
        "second_generator_tasks": len(second_tasks),
        "second_generator_success": second_reactive["overall"]["success_rate"],
        "clear_v1_tasks": len(clear_v1_tasks),
        "clear_v1_splits": clear_v1_manifest["splits"],
        "clear_v1_canonical_sha256": clear_v1_manifest["canonical_sha256"],
        "clear_v1_current_rule_success": clear_v1_baselines["current-rule"][
            "success_rate"
        ],
        "clear_v1_sticky_first_rule_success": clear_v1_baselines[
            "sticky-first-rule"
        ]["success_rate"],
        "model_protocol_id": model_protocol["protocol"]["protocol_id"],
        "model_protocol_sha256": model_protocol["protocol"]["protocol_sha256"],
        "model_protocol_dry_run_tasks": model_protocol["config"][
            "dry_run_tasks"
        ],
        "model_protocol_test_status": model_protocol["test_split_status"],
        "model_protocol_valid_fixture_success": model_protocol["policies"][
            "valid-fixture"
        ]["success_rate"],
        "model_protocol_mixed_fixture_success": model_protocol["policies"][
            "mixed-failure-fixture"
        ]["success_rate"],
    }


def _p2_summary(quick: bool) -> dict:
    tasks = generate_fault_tasks()
    matrix = run_failure_matrix()
    recovery = run_recovery_matrix()
    real_faults = run_real_fault_matrix()
    variants = [
        evaluate(tasks, ReactiveSpecPolicy, "reactive-spec"),
        evaluate(
            tasks,
            lambda: ConfigurableSpecPolicy(
                retain_rule=False,
                retry_on_error=False,
            ),
            "abort-on-fault",
        ),
    ]
    return {
        "status": "implemented-v2",
        "tasks": len(tasks),
        "recovery_rate": variants[0]["overall"]["faulted_recovery_rate"],
        "abort_rate": 1.0 - (variants[1]["overall"]["faulted_recovery_rate"] or 0.0),
        "recoverable_transient_faults": matrix["recoverable"],
        "fatal_unrecoverable_faults": matrix["fatal"],
        "failure_matrix": matrix["rows"],
        "recovery_controllers": {
            name: {
                "success_rate": result["success_rate"],
                "mean_steps": result["steps"],
                "human_interventions": result["human_interventions"],
                "replans": result["replans"],
            }
            for name, result in recovery["by_policy"].items()
        },
        "real_faults": {
            name: {
                "success_rate": values["success_rate"],
                "mean_attempts": values["mean_attempts"],
                "rollbacks": values["rollbacks"],
                "replans": values["replans"],
            }
            for name, values in real_faults["by_policy"].items()
        },
        "quick_mode": quick,
    }


def _p3_summary(quick: bool) -> dict:
    scenarios = 8 if quick else 24
    result = evaluate_memory_scenarios(count=scenarios)
    adversarial = run_adversarial_memory_probe(
        episodes=20 if quick else 100
    )
    layered = run_layered_memory_probe(
        episodes=20 if quick else 100,
        seed=20261028,
    )
    persistent = run_persistent_memory_probe(episodes=8 if quick else 32)
    return {
        "status": "implemented-v2",
        "scenarios": scenarios,
        "recency_only_poison_rate": result["policies"]["recency-only"][
            "poison_rate"
        ],
        "provenance_poison_rate": result["policies"]["provenance-aware"][
            "poison_rate"
        ],
        "adversarial_poison_event_rate": adversarial["policies"]["recency"][
            "poison_event_rate"
        ],
        "adversarial_provenance_poison_event_rate": adversarial["policies"][
            "source-trust"
        ]["poison_event_rate"],
        "adversarial_events": adversarial["event_counts"],
        "layered_layers": layered["config"]["layers"],
        "layered_flat_poison_rate": layered["policies"]["flat-rag"][
            "poison_rate"
        ],
        "layered_provenance_poison_rate": layered["policies"][
            "layered-provenance"
        ]["poison_rate"],
        "layered_final_correct_rate": layered["policies"][
            "layered-provenance"
        ]["final_correct_rate"],
        "layered_conflict_cases": layered["conflict_cases"],
        "persistent_memory": persistent["metrics"],
    }


def _p4_summary() -> dict:
    probe = run_world_model_probe(seed=20261028)
    calibration = run_world_model_calibration_probe(seed=20261028)
    lag1 = probe["models"]["lag-1"]
    lag2 = probe["models"]["lag-2"]
    return {
        "status": "cpu-symbolic-probe",
        "model": "conditional next-symbol table",
        "lag1_accuracy": lag1["one_step_accuracy"],
        "lag2_accuracy": lag2["one_step_accuracy"],
        "lag2_minus_lag1": (
            lag2["one_step_accuracy"] - lag1["one_step_accuracy"]
        ),
        "lag2_rollout_accuracy": lag2["rollout_accuracy"],
        "calibration_id_accuracy": calibration["metrics"]["id_accuracy"],
        "calibration_ood_accuracy": calibration["metrics"]["ood_accuracy"],
        "calibration_id_uncertainty": calibration["metrics"][
            "id_mean_uncertainty"
        ],
        "calibration_ood_uncertainty": calibration["metrics"][
            "ood_mean_uncertainty"
        ],
        "calibration_ood_error_auroc": calibration["metrics"][
            "ood_error_auroc"
        ],
        "calibration_planning_argmax": calibration["planning"]["argmax"][
            "success_rate"
        ],
        "calibration_planning_uncertainty": calibration["planning"][
            "uncertainty_penalized"
        ]["success_rate"],
    }


def _p5_summary() -> dict:
    result = audit_control_suite()
    ablation = EvidenceGate().run_ablation()
    agent = run_research_agent_probe()
    confounding = run_confounding_control_probe()
    claim_schema = run_claim_schema_probe()
    control = confounding["confounding_control"]
    schema_control = claim_schema["confounding_control"]
    schema_decisions = claim_schema["decision_counts"]
    return {
        "status": "implemented-v2",
        "controls": result["controls"],
        "all_expected": result["all_expected"],
        "accepted_valid": result["rows"][0]["gate_passed"],
        "rejected": sum(not row["gate_passed"] for row in result["rows"]),
        "ablation_all_expected": ablation["all_ablation_effects_correct"],
        "research_agent_cases": agent["cases"],
        "naive_false_discoveries": agent["policies"]["naive"][
            "false_discoveries"
        ],
        "gated_false_discoveries": agent["policies"]["gated"][
            "false_discoveries"
        ],
        "gated_valid_discovery_rate": agent["policies"]["gated"][
            "valid_discovery_rate"
        ],
        "confounding_blind_spot_cases": agent["confounding_blind_spot"][
            "cases"
        ],
        "confounding_control_status": confounding["status"],
        "confounding_control_scientific_result": confounding[
            "scientific_result"
        ],
        "confounding_control_cases": confounding["cases"],
        "confounding_declared_detected": control[
            "confounded_declared_detected"
        ],
        "confounding_undeclared_detected": control[
            "confounded_undeclared_detected"
        ],
        "confounding_residual_blind_spot_cases": control[
            "residual_blind_spot_cases"
        ],
        "confounding_false_alarms_on_valid_cases": control[
            "false_alarms_on_valid_cases"
        ],
        "confounding_naive_false_discoveries": confounding["policies"][
            "naive"
        ]["false_discoveries"],
        "confounding_v0_false_discoveries": confounding["policies"][
            "gated_v0"
        ]["false_discoveries"],
        "confounding_v1_false_discoveries": confounding["policies"][
            "gated_v1"
        ]["false_discoveries"],
        "claim_schema_cases": claim_schema["cases"],
        "claim_schema_naive_false_discoveries": claim_schema["policies"][
            "naive"
        ]["false_discoveries"],
        "claim_schema_v1_false_discoveries": claim_schema["policies"][
            "gated_v1"
        ]["false_discoveries"],
        "claim_schema_strict_false_discoveries": claim_schema["policies"][
            "strict_v2"
        ]["false_discoveries"],
        "claim_schema_strict_valid_discovery_rate": claim_schema["policies"][
            "strict_v2"
        ]["valid_discovery_rate"],
        "claim_schema_accepted": schema_decisions["accepted"],
        "claim_schema_rejected": schema_decisions["rejected"],
        "claim_schema_non_evaluable": schema_decisions["non-evaluable"],
        "claim_schema_invalid_declarations": claim_schema["schema_control"][
            "invalid_schema_rejected"
        ],
        "claim_schema_undeclared_confounding_detected": schema_control[
            "confounded_undeclared_detected"
        ],
        "claim_schema_undeclared_confounding_blocked": schema_control[
            "confounded_undeclared_blocked_non_evaluable"
        ],
        "claim_schema_valid_undeclared_blocked": claim_schema[
            "valid_undeclared_cost"
        ]["non_evaluable_claims"],
    }


def _p6_summary() -> dict:
    probe = run_goal_drift_probe(seed=20261028)
    monitor = run_goal_drift_monitor_probe(
        seed=20261028,
        episodes=60,
        steps=40,
    )
    return {
        "status": "cpu-symbolic-probe",
        "episodes": probe["config"]["episodes"],
        "pinned_final_accuracy": probe["policies"]["pinned"]["final_accuracy"],
        "recency_final_accuracy": probe["policies"]["recency"][
            "final_accuracy"
        ],
        "recency_drift_rate": probe["policies"]["recency"]["drift_rate"],
        "decay_final_accuracy": probe["policies"]["decay"]["final_accuracy"],
        "monitor_auroc": monitor["metrics"]["auroc"],
        "monitor_false_alarm_rate": monitor["metrics"]["false_alarm_rate"],
        "monitor_early_warning_rate": monitor["metrics"]["early_warning_rate"],
        "monitor_intervention_recovery_rate": monitor["metrics"][
            "intervention_recovery_rate"
        ],
        "monitor_baseline_final_correct_rate": monitor["metrics"][
            "baseline_final_correct_rate"
        ],
        "monitor_monitored_final_correct_rate": monitor["metrics"][
            "monitored_final_correct_rate"
        ],
    }


def _p8_summary() -> dict:
    probe = run_compute_probe(seed=20261028)
    controller = run_adaptive_controller_probe(seed=20261028)
    return {
        "status": "cpu-symbolic-probe",
        "jobs": probe["config"]["jobs"],
        "budget": probe["config"]["budget"],
        "best_policy_by_value": probe["best_policy_by_value"],
        "safe_policy_value_ratio": (
            probe["policies"]["safe-value-density"]["value"]
            / probe["policies"]["value-density"]["value"]
        ),
        "robustness": probe["robustness"],
        "policies": {
            name: {
                "value": result["value"],
                "spent": result["spent"],
                "deadline_misses": result["deadline_misses"],
                "overspend": result["overspend"],
            }
            for name, result in probe["policies"].items()
        },
        "adaptive_controller": {
            "success_rate": controller["policies"]["adaptive"]["success_rate"],
            "mean_cost": controller["policies"]["adaptive"]["mean_cost"],
            "cost_per_success": controller["policies"]["adaptive"][
                "cost_per_success"
            ],
            "stability_range": controller["policies"]["adaptive"][
                "stability_range"
            ],
            "action_counts": controller["policies"]["adaptive"][
                "action_counts"
            ],
            "memory_writes": controller["policies"]["adaptive"]["memory_writes"],
        },
    }


def _p1_summary() -> dict:
    probe = run_verifier_gap_probe(seed=20261028)
    rewards = run_verifier_reward_probe(seed=20261028)
    return {
        "status": "cpu-symbolic-probe",
        "verifier_gap": probe["verifier_gap"],
        "proxy_policy": probe["policies"]["proxy"],
        "true_policy": probe["policies"]["true"],
        "q_learning_proxy_final_true_reward": probe["q_learning"]["proxy"][
            "mean_final_true_reward"
        ],
        "q_learning_true_final_true_reward": probe["q_learning"]["true"][
            "mean_final_true_reward"
        ],
        "reward_modes": {
            name: {
                "id_success_rate": result["id_success_rate"],
                "ood_success_rate": result["ood_success_rate"],
                "ood_transfer_drop": result["ood_transfer_drop"],
                "mean_reasoning_cost": result["mean_reasoning_cost"],
                "reward_hacking_rate": result["reward_hacking_rate"],
            }
            for name, result in rewards["policies"].items()
        },
    }


def run_cpu_program(*, quick: bool = False) -> dict:
    """Run every CPU-first work package currently implemented in the program."""
    estimator = run_estimator_grid(
        repetitions=4 if quick else 200,
        bootstrap_replicates=20 if quick else 299,
        base_seed=20261027,
    )
    loop_audit = run_agent_loop_audit(
        episodes=40 if quick else 200,
        seed=20261028,
    )
    packages = {
        "P1": {
            "name": "Verifier-Gap RL",
            "deliverable": "toy MDP and four-mode reward protocol",
            "evidence": _p1_summary(),
            "next_gate": "real model and training integration",
        },
        "P2": {
            "name": "FailRecover",
            "deliverable": "four-fault recovery matrix and replanning control",
            "evidence": _p2_summary(quick),
            "next_gate": "real OS/browser tasks and model policy",
        },
        "P3": {
            "name": "ProvMem",
            "deliverable": "three-layer provenance memory, conflicts, forgetting",
            "evidence": _p3_summary(quick),
            "next_gate": "external LongMemEval/LoCoMo and persistent storage",
        },
        "P4": {
            "name": "World Model",
            "deliverable": "symbolic calibration, OOD uncertainty, and planning probe",
            "evidence": _p4_summary(),
            "next_gate": "learned transition model with bounded compute",
        },
        "P5": {
            "name": "Evidence Gate",
            "deliverable": (
                "claim checks, 80-case negative-control agent, and a "
                "90-case stratified confounding control plus a 110-case "
                "strict subgroup-schema control"
            ),
            "evidence": _p5_summary(),
            "next_gate": (
                "live research-agent evaluation and declared-subgroup "
                "schema adoption"
            ),
        },
        "P6": {
            "name": "Goal-Drift Probe",
            "deliverable": "synthetic linear monitor and checkpoint intervention",
            "evidence": _p6_summary(),
            "next_gate": "open-weight activation probe",
        },
        "P7": {
            "name": "CLEAR-Bench and attribution",
            "deliverable": "task suite, factorial designs, estimator validity",
            "evidence": {
                **_p7_summary(quick),
                "estimator_status": estimator["status"],
                "estimator_repetitions": estimator["repetitions"],
                "estimator_coverage": estimator["metrics"]["estimation"][
                    "overall_ci_coverage"
                ],
                "estimator_fwer": estimator["metrics"]["multiplicity"]["null"][
                    "fwer"
                ],
                "loop_audit": loop_audit,
            },
            "next_gate": "model-agent evaluation",
        },
        "P8": {
            "name": "Compute Controller",
            "deliverable": "synthetic scheduler and compute-memory contextual bandit",
            "evidence": _p8_summary(),
            "next_gate": "real tool/retriever runtime with cost instrumentation",
        },
    }
    return {
        "schema_version": 1,
        "generated_at": _timestamp(),
        "status": "harness-validation",
        "scientific_result": False,
        "novelty_status": "not-established",
        "quick": quick,
        "work_packages": packages,
        "summary": {
            "completed_cpu_probes": sum(
                package["evidence"]["status"]
                in {
                    "implemented-v0",
                    "implemented-v2",
                    "cpu-symbolic-probe",
                }
                for package in packages.values()
            ),
            "gpu_used": False,
            "external_api_calls": 0,
            "scientific_result": False,
            "long_run_loop": loop_audit,
            "note": (
                "All eight packages have a CPU probe, but P1/P4/P6/P8 are symbolic "
                "or toy controls and are not model-level or AGI evidence."
            ),
        },
    }
