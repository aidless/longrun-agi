from longrun.program import run_cpu_program


def test_program_does_not_equate_symbolic_probes_with_capability():
    result = run_cpu_program(quick=True)
    for name, package in result["work_packages"].items():
        assert package["evidence"]["status"] in {
            "implemented-v0",
            "implemented-v2",
            "cpu-symbolic-probe",
        }
        if name in {"P1", "P4", "P6", "P8"}:
            assert package["evidence"]["status"] == "cpu-symbolic-probe"
    assert result["scientific_result"] is False
    assert result["novelty_status"] == "not-established"


def test_program_reports_second_generator_and_cross_family():
    result = run_cpu_program(quick=True)
    p7 = result["work_packages"]["P7"]["evidence"]
    assert p7["second_generator_tasks"] > 0
    assert p7["second_generator_success"] == 1.0
    assert p7["clear_v1_tasks"] == 300
    assert p7["clear_v1_splits"] == {"train": 180, "dev": 60, "test": 60}
    assert p7["clear_v1_current_rule_success"] == 1.0
    assert p7["clear_v1_sticky_first_rule_success"] < 1.0
    assert set(p7["cross_family_transfer"]) == {
        "extension_to_prefix",
        "prefix_to_suffix",
        "suffix_to_extension",
    }


def test_program_reports_three_layer_memory_contrast():
    result = run_cpu_program(quick=True)
    p3 = result["work_packages"]["P3"]["evidence"]
    assert p3["layered_layers"] == 3
    assert p3["layered_flat_poison_rate"] > 0.0
    assert p3["layered_provenance_poison_rate"] == 0.0
    assert p3["layered_final_correct_rate"] == 1.0


def test_program_reports_replanning_recovery_contrast():
    result = run_cpu_program(quick=True)
    controllers = result["work_packages"]["P2"]["evidence"]["recovery_controllers"]
    assert controllers["retry-only"]["success_rate"] < 1.0
    assert controllers["replan"]["success_rate"] == 1.0
    assert controllers["state-check-replan"]["success_rate"] == 1.0
    assert controllers["replan"]["human_interventions"] == 0


def test_program_reports_real_fault_and_persistent_memory_controls():
    result = run_cpu_program(quick=True)
    p2 = result["work_packages"]["P2"]["evidence"]
    p3 = result["work_packages"]["P3"]["evidence"]
    assert p2["status"] == "implemented-v2"
    assert p2["real_faults"]["retry-only"]["success_rate"] < 1.0
    assert p2["real_faults"]["state-check-replan"]["success_rate"] == 1.0
    assert p2["real_faults"]["replan"]["success_rate"] == 1.0
    assert p3["status"] == "implemented-v2"
    persistent = p3["persistent_memory"]
    assert persistent["reopened_retrieval_correct_rate"] == 1.0
    assert persistent["poison_or_stale_selection_rate"] == 0.0
    assert persistent["rollback_atomic"] is True
    assert persistent["integrity_check"] == "ok"


def test_program_reports_frozen_model_protocol_without_model():
    result = run_cpu_program(quick=True)
    p7 = result["work_packages"]["P7"]["evidence"]
    assert p7["status"] == "implemented-v2"
    assert p7["model_protocol_id"] == "clear-v1-model-eval-v1"
    assert len(p7["model_protocol_sha256"]) == 64
    assert p7["model_protocol_dry_run_tasks"] == 240
    assert p7["model_protocol_test_status"] == "sealed-not-accessed"
    assert p7["model_protocol_valid_fixture_success"] == 1.0
    assert p7["model_protocol_mixed_fixture_success"] < 1.0


def test_program_reports_negative_control_blind_spot():
    result = run_cpu_program(quick=True)
    p5 = result["work_packages"]["P5"]["evidence"]
    assert p5["research_agent_cases"] == 80
    assert p5["gated_false_discoveries"] < p5["naive_false_discoveries"]
    assert p5["confounding_blind_spot_cases"] == 10


def test_program_reports_confounding_control_v1():
    result = run_cpu_program(quick=True)
    p5 = result["work_packages"]["P5"]["evidence"]
    assert p5["confounding_control_cases"] == 90
    assert p5["confounding_declared_detected"] == 10
    assert p5["confounding_undeclared_detected"] == 0
    assert p5["confounding_residual_blind_spot_cases"] == 10
    assert p5["confounding_false_alarms_on_valid_cases"] == 0
    assert p5["confounding_v1_false_discoveries"] == 10
    assert p5["confounding_v0_false_discoveries"] == 20
    assert p5["confounding_naive_false_discoveries"] == 70
    assert p5["confounding_control_status"] == "harness-validation"
    assert p5["confounding_control_scientific_result"] is False


def test_program_reports_strict_subgroup_claim_schema():
    result = run_cpu_program(quick=True)
    p5 = result["work_packages"]["P5"]["evidence"]
    assert p5["claim_schema_cases"] == 110
    assert p5["status"] == "implemented-v2"
    assert p5["claim_schema_naive_false_discoveries"] == 80
    assert p5["claim_schema_v1_false_discoveries"] == 20
    assert p5["claim_schema_strict_false_discoveries"] == 0
    assert p5["claim_schema_strict_valid_discovery_rate"] == 0.5
    assert p5["claim_schema_accepted"] == 20
    assert p5["claim_schema_rejected"] == 70
    assert p5["claim_schema_non_evaluable"] == 20
    assert p5["claim_schema_invalid_declarations"] == 10
    assert p5["claim_schema_undeclared_confounding_detected"] == 0
    assert p5["claim_schema_undeclared_confounding_blocked"] == 10
    assert p5["claim_schema_valid_undeclared_blocked"] == 10


def test_program_reports_goal_drift_monitor_weak_signal():
    result = run_cpu_program(quick=True)
    p6 = result["work_packages"]["P6"]["evidence"]
    assert p6["monitor_auroc"] > 0.6
    assert p6["monitor_early_warning_rate"] == 0.0
    assert (
        p6["monitor_monitored_final_correct_rate"]
        == p6["monitor_baseline_final_correct_rate"]
    )


def test_program_reports_world_model_uncertainty_negative_result():
    result = run_cpu_program(quick=True)
    p4 = result["work_packages"]["P4"]["evidence"]
    assert p4["calibration_ood_accuracy"] < p4["calibration_id_accuracy"]
    assert p4["calibration_ood_uncertainty"] > p4["calibration_id_uncertainty"]
    assert p4["calibration_ood_error_auroc"] <= 1.0
    assert p4["calibration_planning_argmax"] == 0.5
    assert p4["calibration_planning_uncertainty"] == 0.5


def test_program_reports_verifier_reward_tradeoff():
    result = run_cpu_program(quick=True)
    p1 = result["work_packages"]["P1"]["evidence"]["reward_modes"]
    assert set(p1) == {
        "answer",
        "process",
        "self-verification",
        "ensemble-disagreement",
    }
    assert (
        p1["ensemble-disagreement"]["ood_success_rate"]
        > p1["answer"]["ood_success_rate"]
    )
    assert (
        p1["ensemble-disagreement"]["ood_transfer_drop"]
        < p1["answer"]["ood_transfer_drop"]
    )


def test_program_reports_adaptive_controller_negative_result():
    result = run_cpu_program(quick=True)
    p8 = result["work_packages"]["P8"]["evidence"]["adaptive_controller"]
    assert p8["success_rate"] == 0.48333333333333334
    assert p8["memory_writes"] == 0
    assert p8["stability_range"] == 0.041666666666666685
