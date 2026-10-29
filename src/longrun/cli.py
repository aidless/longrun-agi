from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .analysis.factorial import run_estimator_grid
from .agent_loop import run_agent_loop_audit
from .clear.generators import (
    generate_factorial_tasks,
    generate_fault_tasks,
    generate_tasks,
    generate_three_factor_tasks,
)
from .clear.cross_family import run_cross_family_probe
from .clear.failure_matrix import run_failure_matrix
from .clear.recovery import run_recovery_matrix
from .clear.second_generator import (
    generate_second_clear_tasks,
    generate_second_factorial_tasks,
)
from .clear.policies import (
    ConfigurableSpecPolicy,
    MemorySpecPolicy,
    ReactiveSpecPolicy,
    StickySpecPolicy,
)
from .clear.runner import evaluate, factorial_effects
from .controls.claim_gate import run_claim_schema_probe
from .controls.confounding import run_confounding_control_probe
from .controls.evidence import audit_control_suite
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
from .program import run_cpu_program
from .runtime.real_faults import run_real_fault_matrix


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: str | Path, payload: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    destination.write_text(text, encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(f"wrote {destination} sha256={digest}")


def cmd_clear_eval(args: argparse.Namespace) -> int:
    tasks = generate_tasks(instances_per_variant=args.instances)
    reactive = evaluate(tasks, ReactiveSpecPolicy, "reactive-spec")
    sticky = evaluate(tasks, StickySpecPolicy, "sticky-spec")
    payload = {
        "generated_at": _timestamp(),
        "suite": "CLEAR-Bench v0",
        "config": {
            "instances_per_variant": args.instances,
            "tasks": len(tasks),
        },
        "policy_results": {
            "reactive-spec": reactive,
            "sticky-spec": sticky,
        },
        "contrast": {
            "reactive_shift_success_rate": reactive["overall"]["shift_success_rate"],
            "sticky_shift_success_rate": sticky["overall"]["shift_success_rate"],
            "dynamic_range": (
                (reactive["overall"]["shift_success_rate"] or 0.0)
                - (sticky["overall"]["shift_success_rate"] or 0.0)
            ),
        },
    }
    _write_json(args.output, payload)
    print(
        "shift success: "
        f"reactive={payload['contrast']['reactive_shift_success_rate']:.3f} "
        f"sticky={payload['contrast']['sticky_shift_success_rate']:.3f}"
    )
    return 0


def cmd_clear_faults(args: argparse.Namespace) -> int:
    tasks = generate_fault_tasks()
    result = evaluate(tasks, ReactiveSpecPolicy, "reactive-spec")
    payload = {
        "generated_at": _timestamp(),
        "suite": "CLEAR-Bench fault recovery v0",
        "config": {"tasks": len(tasks)},
        "result": result,
    }
    _write_json(args.output, payload)
    print(
        f"fault recovery: {result['overall']['faulted_recoveries']}/"
        f"{result['overall']['faulted_runs']}"
    )
    return 0


def cmd_provmem_audit(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "ProvMem synthetic audit v0",
        **evaluate_memory_scenarios(count=args.scenarios),
    }
    _write_json(args.output, payload)
    for name, result in payload["policies"].items():
        print(
            f"{name}: correct={result['correct_rate']:.3f} "
            f"poison={result['poison_rate']:.3f}"
        )
    return 0


def cmd_controls_audit(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "Evidence Gate synthetic controls v0",
        **audit_control_suite(),
    }
    _write_json(args.output, payload)
    print(f"control expectations matched: {payload['all_expected']}")
    return 0 if payload["all_expected"] else 1


def cmd_research_agent(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "negative-control research agent v0",
        **run_research_agent_probe(),
    }
    _write_json(args.output, payload)
    naive = payload["policies"]["naive"]
    gated = payload["policies"]["gated"]
    print(
        f"naive_false={naive['false_discoveries']} "
        f"gated_false={gated['false_discoveries']} "
        f"blind_spot={payload['confounding_blind_spot']['cases']}"
    )
    return 0


def cmd_confounding_control(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "stratified confounding control v1",
        **run_confounding_control_probe(),
    }
    _write_json(args.output, payload)
    policies = payload["policies"]
    control = payload["confounding_control"]
    print(
        f"naive_false={policies['naive']['false_discoveries']} "
        f"v0_false={policies['gated_v0']['false_discoveries']} "
        f"v1_false={policies['gated_v1']['false_discoveries']} "
        f"declared={control['confounded_declared_detected']}/"
        f"{control['confounded_declared_cases']} "
        f"undeclared={control['confounded_undeclared_detected']}/"
        f"{control['confounded_undeclared_cases']}"
    )
    return 0


def cmd_claim_schema(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "strict subgroup claim schema v2",
        **run_claim_schema_probe(),
    }
    _write_json(args.output, payload)
    policies = payload["policies"]
    decisions = payload["decision_counts"]
    print(
        f"naive_false={policies['naive']['false_discoveries']} "
        f"v1_false={policies['gated_v1']['false_discoveries']} "
        f"strict_false={policies['strict_v2']['false_discoveries']} "
        f"accepted={decisions['accepted']} "
        f"rejected={decisions['rejected']} "
        f"non_evaluable={decisions['non-evaluable']}"
    )
    return 0


def cmd_factorial_eval(args: argparse.Namespace) -> int:
    tasks = generate_factorial_tasks(instances_per_variant=args.instances)
    configurations = {
        "robust": {"retain_rule": False, "retry_on_error": True},
        "no-retry": {"retain_rule": False, "retry_on_error": False},
        "sticky-rule": {"retain_rule": True, "retry_on_error": True},
        "fragile": {"retain_rule": True, "retry_on_error": False},
    }
    policy_results: dict[str, dict] = {}
    for label, config in configurations.items():
        result = evaluate(
            tasks,
            lambda config=config: ConfigurableSpecPolicy(**config),
            label,
        )
        policy_results[label] = {
            "effects": factorial_effects(result),
            "summary": result["overall"],
            "result": result,
        }
    payload = {
        "generated_at": _timestamp(),
        "suite": "CLEAR factorial attribution v0",
        "config": {
            "instances_per_cell": args.instances,
            "tasks": len(tasks),
            "design": "3 families x rule_shift(2) x tool_fault(2) x instances",
        },
        "policy_results": policy_results,
    }
    _write_json(args.output, payload)
    for label, result in payload["policy_results"].items():
        effects = result["effects"]
        print(
            f"{label}: rule={effects['rule_shift_main_effect']:.3f} "
            f"tool={effects['tool_fault_main_effect']:.3f} "
            f"interaction={effects['interaction_rule_x_tool']:.3f}"
        )
    return 0


def cmd_three_factor_eval(args: argparse.Namespace) -> int:
    tasks = generate_three_factor_tasks(instances_per_variant=args.instances)
    configurations = {
        "spec-recheck": lambda: ConfigurableSpecPolicy(
            retain_rule=False, retry_on_error=True
        ),
        "spec-no-retry": lambda: ConfigurableSpecPolicy(
            retain_rule=False, retry_on_error=False
        ),
        "sticky-rule": lambda: ConfigurableSpecPolicy(
            retain_rule=True, retry_on_error=True
        ),
        "fragile-sticky": lambda: ConfigurableSpecPolicy(
            retain_rule=True, retry_on_error=False
        ),
        "memory-naive": lambda: MemorySpecPolicy(
            trusted_memory=False, retry_on_error=True
        ),
        "memory-provenance": lambda: MemorySpecPolicy(
            trusted_memory=True, retry_on_error=True
        ),
    }
    policy_results: dict[str, dict] = {}
    for label, factory in configurations.items():
        result = evaluate(tasks, factory, label)
        policy_results[label] = {
            "effects": factorial_effects(result),
            "summary": result["overall"],
            "result": result,
        }
    payload = {
        "generated_at": _timestamp(),
        "suite": "CLEAR three-factor attribution v0",
        "config": {
            "instances_per_cell": args.instances,
            "tasks": len(tasks),
            "design": (
                "3 families x rule_shift(2) x tool_fault(2) x "
                "memory_poison(2) x instances"
            ),
        },
        "policy_results": policy_results,
    }
    _write_json(args.output, payload)
    for label, result in payload["policy_results"].items():
        effects = result["effects"]
        mains = effects["main_effects"]
        interactions = effects["interactions"]
        three_way_key = next(
            key for key in interactions if key.count("_x_") == 2
        )
        print(
            f"{label}: "
            f"rule={mains['rule_shift']:.3f} "
            f"tool={mains['tool_fault']:.3f} "
            f"memory={mains['memory_poison']:.3f} "
            f"rxt={interactions['rule_shift_x_tool_fault']:.3f} "
            f"three-way={interactions[three_way_key]:.3f}"
        )
    return 0


def cmd_estimator_validity(args: argparse.Namespace) -> int:
    grid = run_estimator_grid(
        repetitions=args.repetitions,
        bootstrap_replicates=args.bootstrap_replicates,
        base_seed=args.seed,
        confidence_level=args.confidence_level,
        alpha=args.alpha,
    )
    payload = {
        "generated_at": _timestamp(),
        "suite": "factorial estimator validity v0",
        **grid,
    }
    _write_json(args.output, payload)
    estimation = payload["metrics"]["estimation"]
    null = payload["metrics"]["multiplicity"]["null"]
    alternative = payload["metrics"]["multiplicity"]["alternative"]
    print(
        f"coverage={estimation['overall_ci_coverage']:.3f} "
        f"fwer={null['fwer']:.3f} "
        f"power={alternative['power_any_true_effect']:.3f} "
        f"fdr={alternative['fdr']:.3f}"
    )
    return 0


def cmd_second_generator(args: argparse.Namespace) -> int:
    tasks = generate_second_clear_tasks(
        instances_per_variant=args.instances,
        seed=args.seed,
    )
    reactive = evaluate(
        tasks,
        lambda: ReactiveSpecPolicy(source_dir="queue"),
        "reactive-second",
    )
    sticky = evaluate(
        tasks,
        lambda: StickySpecPolicy(source_dir="queue"),
        "sticky-second",
    )
    payload = {
        "generated_at": _timestamp(),
        "suite": "second independent CLEAR generator v0",
        "config": {"instances": args.instances, "seed": args.seed},
        "tasks": len(tasks),
        "results": {"reactive": reactive, "sticky": sticky},
    }
    _write_json(args.output, payload)
    print(
        f"tasks={len(tasks)} reactive={reactive['overall']['success_rate']:.3f} "
        f"sticky_shift={sticky['overall']['shift_success_rate']:.3f}"
    )
    return 0


def cmd_probes(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "CPU symbolic probes v0",
        "probes": {
            "verifier-gap": run_verifier_gap_probe(seed=args.seed),
            "world-model": run_world_model_probe(seed=args.seed),
            "goal-drift": run_goal_drift_probe(seed=args.seed),
            "compute": run_compute_probe(seed=args.seed),
            "cross-family": run_cross_family_probe(seed=args.seed),
        },
    }
    _write_json(args.output, payload)
    return 0


def cmd_failure_matrix(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "tool failure matrix v0",
        **run_failure_matrix(),
    }
    _write_json(args.output, payload)
    print(
        f"recoverable={payload['recoverable']} fatal={payload['fatal']}"
    )
    return 0


def cmd_recovery_matrix(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "failure recovery matrix v0",
        **run_recovery_matrix(),
    }
    _write_json(args.output, payload)
    print(
        f"replan={payload['by_policy']['replan']['success_rate']:.3f} "
        f"state_check={payload['by_policy']['state-check-replan']['success_rate']:.3f}"
    )
    return 0


def cmd_adversarial_memory(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "adversarial memory v0",
        **run_adversarial_memory_probe(
            seed=args.seed,
            episodes=args.episodes,
        ),
    }
    _write_json(args.output, payload)
    print(
        "recency_poison_event_rate="
        f"{payload['policies']['recency']['poison_event_rate']:.3f} "
        "provenance_poison_event_rate="
        f"{payload['policies']['source-trust']['poison_event_rate']:.3f}"
    )
    return 0


def cmd_layered_memory(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "layered memory probe v0",
        **run_layered_memory_probe(
            seed=args.seed,
            episodes=args.episodes,
        ),
    }
    _write_json(args.output, payload)
    flat = payload["policies"]["flat-rag"]
    layered = payload["policies"]["layered-provenance"]
    print(
        f"flat_poison={flat['poison_rate']:.3f} "
        f"layered_poison={layered['poison_rate']:.3f} "
        f"layers={payload['config']['layers']}"
    )
    return 0


def cmd_persistent_memory(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "persistent SQLite memory v0",
        **run_persistent_memory_probe(episodes=args.episodes),
    }
    _write_json(args.output, payload)
    metrics = payload["metrics"]
    print(
        f"reopen={metrics['reopened_retrieval_correct_rate']:.3f} "
        f"poison={metrics['poison_or_stale_selection_rate']:.3f} "
        f"rollback={metrics['rollback_atomic']} "
        f"integrity={metrics['integrity_check']}"
    )
    return 0


def cmd_model_protocol(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        **run_model_protocol_dry_run(),
    }
    _write_json(args.output, payload)
    valid = payload["policies"]["valid-fixture"]
    mixed = payload["policies"]["mixed-failure-fixture"]
    print(
        f"dry_run={payload['config']['dry_run_tasks']} "
        f"test={payload['test_split_status']} "
        f"valid={valid['success_rate']:.3f} "
        f"mixed={mixed['success_rate']:.3f}"
    )
    return 0


def cmd_real_faults(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "real filesystem and subprocess recovery v0",
        **run_real_fault_matrix(),
    }
    _write_json(args.output, payload)
    policies = payload["by_policy"]
    print(
        f"retry={policies['retry-only']['success_rate']:.3f} "
        f"rollback={policies['rollback']['success_rate']:.3f} "
        f"state_check={policies['state-check-replan']['success_rate']:.3f} "
        f"replan={policies['replan']['success_rate']:.3f}"
    )
    return 0


def cmd_agent_loop(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "long-run loop audit v0",
        **run_agent_loop_audit(episodes=args.episodes, seed=args.seed),
    }
    _write_json(args.output, payload)
    print(
        f"resume={payload['resume_success']} "
        f"trace_hash={payload['all_traces_hash_valid']}"
    )
    return 0


def cmd_goal_drift_monitor(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "goal drift monitor v0",
        **run_goal_drift_monitor_probe(
            seed=args.seed,
            episodes=args.episodes,
            steps=args.steps,
        ),
    }
    _write_json(args.output, payload)
    print(
        f"auroc={payload['metrics']['auroc']:.3f} "
        f"false_alarm={payload['metrics']['false_alarm_rate']:.3f} "
        f"monitored_final={payload['metrics']['monitored_final_correct_rate']:.3f}"
    )
    return 0


def cmd_world_model_calibration(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "calibrated world model v0",
        **run_world_model_calibration_probe(
            seed=args.seed,
            samples_per_pair=args.samples,
        ),
    }
    _write_json(args.output, payload)
    print(
        f"id={payload['metrics']['id_accuracy']:.3f} "
        f"ood={payload['metrics']['ood_accuracy']:.3f} "
        f"ood_unc={payload['metrics']['ood_mean_uncertainty']:.3f}"
    )
    return 0


def cmd_verifier_rewards(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "verifier reward protocol v0",
        **run_verifier_reward_probe(
            seed=args.seed,
            train_episodes=args.train_episodes,
        ),
    }
    _write_json(args.output, payload)
    print(
        "answer_ood="
        f"{payload['policies']['answer']['ood_success_rate']:.3f} "
        "ensemble_ood="
        f"{payload['policies']['ensemble-disagreement']['ood_success_rate']:.3f}"
    )
    return 0


def cmd_adaptive_controller(args: argparse.Namespace) -> int:
    payload = {
        "generated_at": _timestamp(),
        "suite": "adaptive compute-memory controller v0",
        **run_adaptive_controller_probe(
            seed=args.seed,
            train_episodes=args.train_episodes,
        ),
    }
    _write_json(args.output, payload)
    adaptive = payload["policies"]["adaptive"]
    print(
        f"success={adaptive['success_rate']:.3f} "
        f"cost={adaptive['mean_cost']:.3f} "
        f"stability={adaptive['stability_range']:.3f}"
    )
    return 0


def cmd_program(args: argparse.Namespace) -> int:
    payload = run_cpu_program(quick=args.quick)
    _write_json(args.output, payload)
    print(
        f"cpu_probes={payload['summary']['completed_cpu_probes']}/8 "
        f"gpu={payload['summary']['gpu_used']}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="longrun")
    subparsers = parser.add_subparsers(dest="command", required=True)

    clear_eval = subparsers.add_parser("clear-eval", help="run paired rule-shift tasks")
    clear_eval.add_argument("--instances", type=int, default=4)
    clear_eval.add_argument("--output", required=True)
    clear_eval.set_defaults(func=cmd_clear_eval)

    clear_faults = subparsers.add_parser("clear-faults", help="run fault recovery tasks")
    clear_faults.add_argument("--output", required=True)
    clear_faults.set_defaults(func=cmd_clear_faults)

    provmem = subparsers.add_parser("provmem-audit", help="run memory poison audit")
    provmem.add_argument("--scenarios", type=int, default=24)
    provmem.add_argument("--output", required=True)
    provmem.set_defaults(func=cmd_provmem_audit)

    controls = subparsers.add_parser("controls-audit", help="run negative-control gate")
    controls.add_argument("--output", required=True)
    controls.set_defaults(func=cmd_controls_audit)

    research_agent = subparsers.add_parser(
        "research-agent",
        help="run 80-case negative-control research agent probe",
    )
    research_agent.add_argument("--output", required=True)
    research_agent.set_defaults(func=cmd_research_agent)

    confounding = subparsers.add_parser(
        "confounding-control",
        help="run the 90-case stratified confounding control",
    )
    confounding.add_argument("--output", required=True)
    confounding.set_defaults(func=cmd_confounding_control)

    claim_schema = subparsers.add_parser(
        "claim-schema",
        help="run the 110-case strict subgroup claim-schema control",
    )
    claim_schema.add_argument("--output", required=True)
    claim_schema.set_defaults(func=cmd_claim_schema)

    factorial = subparsers.add_parser(
        "factorial-eval",
        help="run 2x2 rule-shift/tool-fault attribution suite",
    )
    factorial.add_argument("--instances", type=int, default=4)
    factorial.add_argument("--output", required=True)
    factorial.set_defaults(func=cmd_factorial_eval)

    three_factor = subparsers.add_parser(
        "three-factor-eval",
        help="run rule-shift x tool-fault x memory-poison attribution suite",
    )
    three_factor.add_argument("--instances", type=int, default=4)
    three_factor.add_argument("--output", required=True)
    three_factor.set_defaults(func=cmd_three_factor_eval)

    estimator = subparsers.add_parser(
        "estimator-validity",
        help="run fixed-seed Monte Carlo checks for factorial inference",
    )
    estimator.add_argument("--repetitions", type=int, default=200)
    estimator.add_argument("--bootstrap-replicates", type=int, default=299)
    estimator.add_argument("--seed", type=int, default=20261027)
    estimator.add_argument("--confidence-level", type=float, default=0.95)
    estimator.add_argument("--alpha", type=float, default=0.05)
    estimator.add_argument("--output", required=True)
    estimator.set_defaults(func=cmd_estimator_validity)

    second = subparsers.add_parser(
        "second-generator",
        help="run the structurally independent CLEAR generator",
    )
    second.add_argument("--instances", type=int, default=4)
    second.add_argument("--seed", type=int, default=20261028)
    second.add_argument("--output", required=True)
    second.set_defaults(func=cmd_second_generator)

    probes = subparsers.add_parser(
        "probes",
        help="run P1/P4/P6/P8 and cross-family symbolic probes",
    )
    probes.add_argument("--seed", type=int, default=20261028)
    probes.add_argument("--output", required=True)
    probes.set_defaults(func=cmd_probes)

    failures = subparsers.add_parser(
        "failure-matrix",
        help="run recoverable and fatal tool fault matrix",
    )
    failures.add_argument("--output", required=True)
    failures.set_defaults(func=cmd_failure_matrix)

    recovery = subparsers.add_parser(
        "recovery-matrix",
        help="run stale/tool/doc/rule-change recovery comparisons",
    )
    recovery.add_argument("--output", required=True)
    recovery.set_defaults(func=cmd_recovery_matrix)

    adversarial = subparsers.add_parser(
        "adversarial-memory",
        help="run mixed poison, expiry, and supersession checks",
    )
    adversarial.add_argument("--episodes", type=int, default=100)
    adversarial.add_argument("--seed", type=int, default=20261028)
    adversarial.add_argument("--output", required=True)
    adversarial.set_defaults(func=cmd_adversarial_memory)

    layered = subparsers.add_parser(
        "layered-memory",
        help="run episodic/semantic/procedural memory probe",
    )
    layered.add_argument("--episodes", type=int, default=100)
    layered.add_argument("--seed", type=int, default=20261028)
    layered.add_argument("--output", required=True)
    layered.set_defaults(func=cmd_layered_memory)

    persistent = subparsers.add_parser(
        "persistent-memory",
        help="run SQLite restart, rollback, conflict, and import/export checks",
    )
    persistent.add_argument("--episodes", type=int, default=32)
    persistent.add_argument("--output", required=True)
    persistent.set_defaults(func=cmd_persistent_memory)

    model_protocol = subparsers.add_parser(
        "model-protocol",
        help="run the frozen CLEAR-300-v1 train/dev fake-model dry run",
    )
    model_protocol.add_argument("--output", required=True)
    model_protocol.set_defaults(func=cmd_model_protocol)

    real_faults = subparsers.add_parser(
        "real-faults",
        help="run recovery controls over temporary files and subprocesses",
    )
    real_faults.add_argument("--output", required=True)
    real_faults.set_defaults(func=cmd_real_faults)

    loop = subparsers.add_parser(
        "agent-loop",
        help="run trace, duplicate-action, and resume checks",
    )
    loop.add_argument("--episodes", type=int, default=200)
    loop.add_argument("--seed", type=int, default=20261028)
    loop.add_argument("--output", required=True)
    loop.set_defaults(func=cmd_agent_loop)

    goal_monitor = subparsers.add_parser(
        "goal-drift-monitor",
        help="run synthetic goal-drift trajectory monitor",
    )
    goal_monitor.add_argument("--episodes", type=int, default=60)
    goal_monitor.add_argument("--steps", type=int, default=40)
    goal_monitor.add_argument("--seed", type=int, default=20261028)
    goal_monitor.add_argument("--output", required=True)
    goal_monitor.set_defaults(func=cmd_goal_drift_monitor)

    world_calibration = subparsers.add_parser(
        "world-model-calibration",
        help="run calibrated symbolic world-model probe",
    )
    world_calibration.add_argument("--samples", type=int, default=20)
    world_calibration.add_argument("--seed", type=int, default=20261028)
    world_calibration.add_argument("--output", required=True)
    world_calibration.set_defaults(func=cmd_world_model_calibration)

    verifier_rewards = subparsers.add_parser(
        "verifier-rewards",
        help="compare answer/process/self/ensemble verifier rewards",
    )
    verifier_rewards.add_argument("--train-episodes", type=int, default=600)
    verifier_rewards.add_argument("--seed", type=int, default=20261028)
    verifier_rewards.add_argument("--output", required=True)
    verifier_rewards.set_defaults(func=cmd_verifier_rewards)

    adaptive_controller = subparsers.add_parser(
        "adaptive-controller",
        help="train contextual compute-memory controller on CLEAR contexts",
    )
    adaptive_controller.add_argument("--train-episodes", type=int, default=600)
    adaptive_controller.add_argument("--seed", type=int, default=20261028)
    adaptive_controller.add_argument("--output", required=True)
    adaptive_controller.set_defaults(func=cmd_adaptive_controller)

    program = subparsers.add_parser(
        "program",
        help="run and summarize all eight CPU work packages",
    )
    program.add_argument("--quick", action="store_true")
    program.add_argument("--output", required=True)
    program.set_defaults(func=cmd_program)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
