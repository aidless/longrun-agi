"""Model-facing CLEAR-300-v1 protocol with model-free dry-run checks."""

from __future__ import annotations

import hashlib
import json

from ..benchmarks.clear_v1 import (
    ClearTask,
    build_split_manifest,
    generate_clear_v1_tasks,
)


PROTOCOL_ID = "clear-v1-model-eval-v1"
PROTOCOL_VERSION = 1
DRY_RUN_SPLITS = ("train", "dev")


def _canonical(payload: object) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _sha256(payload: object) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def build_model_protocol(tasks: list[ClearTask]) -> dict:
    split_manifest = build_split_manifest(tasks, seed=20261028)
    protocol = {
        "schema_version": PROTOCOL_VERSION,
        "protocol_id": PROTOCOL_ID,
        "benchmark": "CLEAR-300-v1",
        "benchmark_task_manifest_sha256": split_manifest["canonical_sha256"],
        "splits": {
            "train": 180,
            "dev": 60,
            "test": 60,
            "dry_run_allowed": list(DRY_RUN_SPLITS),
            "test_status": "sealed-not-accessed",
        },
        "prompt_template": (
            "You are evaluating a long-horizon agent environment task.\n"
            "Read the task instruction and initial state, apply the current "
            "authoritative rule, and return only JSON matching the response "
            "schema. Do not use cached rules when the current specification "
            "differs.\n\n"
            "<TASK>\n{task_json}\n</TASK>\n"
        ),
        "response_schema": {
            "type": "object",
            "required": ["output"],
            "properties": {
                "output": {"type": "object"},
                "reasoning_summary": {"type": "string"},
                "abstain": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
        "scoring": {
            "success": "response.output equals task.expected",
            "abstention_is_success": False,
            "malformed_response_is_success": False,
            "timeout_is_success": False,
            "retry_policy": "record every attempt and score the final attempt",
            "metrics": [
                "success_rate",
                "valid_json_rate",
                "schema_valid_rate",
                "timeout_rate",
                "error_rate",
                "tokens_in",
                "tokens_out",
                "latency_ms",
            ],
        },
        "failure_taxonomy": [
            "timeout",
            "transport-error",
            "invalid-json",
            "schema-invalid",
            "wrong-output",
            "abstained",
        ],
        "execution_contract": {
            "model_downloaded": False,
            "model_loaded": False,
            "network_calls": 0,
            "paid_api_calls": 0,
            "test_split_accessed": False,
        },
    }
    return {
        **protocol,
        "protocol_sha256": _sha256(protocol),
    }


def evaluate_model_response(
    task: ClearTask,
    response: dict,
) -> dict:
    status = response.get("status", "ok")
    output = response.get("output")
    if status != "ok":
        return {
            "task_id": task.task_id,
            "success": False,
            "valid_json": status != "invalid-json",
            "schema_valid": False,
            "failure": status,
        }
    if not isinstance(output, dict):
        return {
            "task_id": task.task_id,
            "success": False,
            "valid_json": True,
            "schema_valid": False,
            "failure": "schema-invalid",
        }
    if output != task.expected:
        failure = "abstained" if response.get("abstain") else "wrong-output"
        return {
            "task_id": task.task_id,
            "success": False,
            "valid_json": True,
            "schema_valid": True,
            "failure": failure,
        }
    return {
        "task_id": task.task_id,
        "success": True,
        "valid_json": True,
        "schema_valid": True,
        "failure": None,
    }


def _response(
    task: ClearTask,
    *,
    status: str = "ok",
    output: dict | None = None,
) -> dict:
    return {
        "task_id": task.task_id,
        "status": status,
        "output": task.expected if output is None and status == "ok" else output,
        "tokens_in": (len(task.instruction) + 3) // 4,
        "tokens_out": 0 if status != "ok" else 16,
        "latency_ms": 10 if status == "ok" else 250,
    }


def _policy_summary(
    tasks: list[ClearTask],
    responses: list[dict],
) -> dict:
    rows = [
        evaluate_model_response(task, response)
        for task, response in zip(tasks, responses, strict=True)
    ]
    counts: dict[str, int] = {}
    for row in rows:
        if row["failure"] is not None:
            counts[row["failure"]] = counts.get(row["failure"], 0) + 1
    return {
        "tasks": len(rows),
        "successes": sum(row["success"] for row in rows),
        "success_rate": sum(row["success"] for row in rows) / len(rows),
        "valid_json_rate": sum(row["valid_json"] for row in rows) / len(rows),
        "schema_valid_rate": (
            sum(row["schema_valid"] for row in rows) / len(rows)
        ),
        "failure_counts": counts,
        "tokens_in": sum(response["tokens_in"] for response in responses),
        "tokens_out": sum(response["tokens_out"] for response in responses),
        "latency_ms": sum(response["latency_ms"] for response in responses),
    }


def run_model_protocol_dry_run(
    tasks: list[ClearTask] | None = None,
) -> dict:
    if tasks is None:
        tasks = generate_clear_v1_tasks(seed=20261028)
    protocol = build_model_protocol(tasks)
    dry_run_tasks = [
        task for task in tasks if task.split in DRY_RUN_SPLITS
    ]
    valid_responses = [_response(task) for task in dry_run_tasks]
    mixed_responses: list[dict] = []
    mixed_rows: list[dict] = []
    for index, task in enumerate(dry_run_tasks):
        if index % 19 == 0:
            response = _response(task, status="timeout", output=None)
        elif index % 17 == 0:
            response = _response(task, status="invalid-json", output=None)
        elif index % 23 == 0:
            response = _response(task, output={"unexpected": True})
        else:
            response = _response(task)
        mixed_responses.append(response)
        scored = evaluate_model_response(task, response)
        mixed_rows.append(
            {
                **scored,
                "output_sha256": _sha256(response["output"]),
            }
        )
    return {
        "status": "harness-validation",
        "scientific_result": False,
        "novelty_status": "not-established",
        "config": {
            "protocol_id": PROTOCOL_ID,
            "protocol_version": PROTOCOL_VERSION,
            "dry_run_tasks": len(dry_run_tasks),
            "test_tasks": sum(task.split == "test" for task in tasks),
            "model_downloaded": False,
            "model_loaded": False,
            "network_calls": 0,
            "paid_api_calls": 0,
        },
        "protocol": protocol,
        "policies": {
            "valid-fixture": _policy_summary(dry_run_tasks, valid_responses),
            "mixed-failure-fixture": _policy_summary(
                dry_run_tasks, mixed_responses
            ),
        },
        "test_split_status": "sealed-not-accessed",
        "mixed_response_hashes": _sha256(mixed_rows),
        "notes": [
            "Both policies are deterministic fixtures, not model outputs.",
            "The dry run uses only the 240 train/dev tasks.",
            "The frozen test split is not accessed or scored.",
        ],
    }
