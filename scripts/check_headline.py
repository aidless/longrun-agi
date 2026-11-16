"""Recompute the one closed result and fail if the public claim drifts.

The closed result is recovery-matrix v1 on scripted controllers. Rates are
aggregated from the committed episode rows. Those rows are replayed on the
frozen task file. CLEAR-300-v1 is checked only as a frozen split, not as
this result. No network, model, or GPU.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from longrun.benchmarks.clear_v1 import (  # noqa: E402
    build_split_manifest,
    generate_clear_v1_tasks,
)
from longrun.clear.recovery import (  # noqa: E402
    FaultKind,
    RecoveryTask,
    run_recovery_matrix,
)


TASK_FILE = ROOT / "benchmarks/recovery-matrix-v1/tasks.json"
TRACE_FILE = (
    ROOT / "artifacts/recovery-v0/v2/results/recovery-matrix.json"
)
CLEAR_MANIFEST = ROOT / "benchmarks/clear-300-v1/split-manifest.json"
README = ROOT / "README.md"
RELEASE_COMMIT_FILE = ROOT / "benchmarks/recovery-matrix-v1/release-commit.txt"
PROBLEM_START = "<!-- problem:start -->"
PROBLEM_END = "<!-- problem:end -->"
HEADLINE_START = "<!-- headline-result:start -->"
HEADLINE_END = "<!-- headline-result:end -->"
BANNED_PAGE_CLAIMS = ("60→0", "60 → 0", "5 / 5")
PAGE_GLOBS = ("docs/**/*.html", "docs/**/*.js")
CORPUS_GLOBS = (
    "artifacts/**/*.json",
    "artifacts/**/*.md",
    "benchmarks/clear-300-v1/**/*.json",
    "benchmarks/clear-300-v1/**/*.md",
    "benchmarks/recovery-matrix-v1/**/*.json",
    "benchmarks/recovery-matrix-v1/**/*.md",
    "experiments/**/results/*.json",
    "PORTFOLIO-STATUS.md",
    "CHANGELOG.md",
    "pyproject.toml",
    ".github/workflows/*.yml",
)
NUMBER_RE = re.compile(r"\d+\.\d+(?:\.\d+)?|\d+\s*/\s*\d+")
VERSION_RE = re.compile(r"\bv?\d+\.\d+\.\d+\b")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _format_rate(rate: float) -> str:
    text = f"{rate:.4f}".rstrip("0").rstrip(".")
    if "." not in text:
        text += ".0"
    return text


def load_frozen_tasks() -> list[RecoveryTask]:
    payload = _load_json(TASK_FILE)
    tasks = []
    for item in payload["tasks"]:
        tasks.append(
            RecoveryTask(
                task_id=item["task_id"],
                fault_kind=FaultKind(item["fault_kind"]),
                initial_rule=item["initial_rule"],
                corrected_rule=item["corrected_rule"],
                max_steps=int(item["max_steps"]),
            )
        )
    return tasks


def load_committed_rows() -> list[dict[str, Any]]:
    payload = _load_json(TRACE_FILE)
    rows = payload["rows"]
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{TRACE_FILE} has no episode rows")
    return rows


def _row_key(row: dict[str, Any]) -> str:
    return json.dumps(
        {
            "task_id": row["task_id"],
            "fault_kind": row["fault_kind"],
            "policy": row["policy"],
            "success": row["success"],
            "steps": row["steps"],
            "human_intervention": row["human_intervention"],
            "replans": row["replans"],
            "rollbacks": row["rollbacks"],
            "tool_failures": row["tool_failures"],
            "error": row["error"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def aggregate_rates(rows: list[dict[str, Any]]) -> dict[str, str]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["policy"], []).append(row)
    return {
        policy: _format_rate(
            sum(bool(row["success"]) for row in items) / len(items)
        )
        for policy, items in sorted(grouped.items())
    }


def retry_like_only_on_tool_error(rows: list[dict[str, Any]]) -> bool:
    for policy in ("retry-only", "rollback"):
        selected = [row for row in rows if row["policy"] == policy]
        if not selected:
            return False
        for row in selected:
            expect = row["fault_kind"] == "tool_error"
            if bool(row["success"]) is not expect:
                return False
    return True


def recompute_clear_canonical_sha256() -> str:
    manifest = _load_json(CLEAR_MANIFEST)
    generated = generate_clear_v1_tasks(seed=int(manifest["seed"]))
    expected = build_split_manifest(generated, seed=int(manifest["seed"]))
    if manifest["canonical_sha256"] != expected["canonical_sha256"]:
        raise ValueError("CLEAR-300-v1 canonical_sha256 does not match a rebuild")
    if manifest["splits"] != {"train": 180, "dev": 60, "test": 60}:
        raise ValueError("CLEAR-300-v1 split counts are not 180/60/60")
    if manifest.get("frozen") is not True:
        raise ValueError("CLEAR-300-v1 manifest is not marked frozen")
    if len(manifest["tasks"]) != 300:
        raise ValueError("CLEAR-300-v1 manifest does not list 300 tasks")
    return expected["canonical_sha256"]


def headline_block(rates: dict[str, str], canonical_sha256: str) -> str:
    lines = [
        "result_id: recovery-matrix-v1",
        "controllers: scripted",
        "tasks: 40",
        "traces: 160",
        f"replan: {rates['replan']}",
        f"state-check-replan: {rates['state-check-replan']}",
        f"retry-only: {rates['retry-only']}",
        f"rollback: {rates['rollback']}",
        "retry_and_rollback_succeed_only_on: tool_error",
        f"clear-300-v1-canonical-sha256: {canonical_sha256}",
        "clear-300-v1-splits: 180/60/60",
        "human_annotation: not-done",
        "model_gate: hold",
    ]
    return "\n".join(lines)


def _between(text: str, start: str, end: str) -> str:
    begin = text.find(start)
    finish = text.find(end)
    if begin < 0 or finish < 0 or finish < begin:
        raise ValueError(f"missing markers {start} / {end}")
    return text[begin + len(start) : finish].strip("\n")


def check_readme(block: str, rates: dict[str, str]) -> list[str]:
    errors: list[str] = []
    text = README.read_text(encoding="utf-8")
    try:
        problem = _between(text, PROBLEM_START, PROBLEM_END)
    except ValueError as exc:
        return [str(exc)]
    problem_lines = [line for line in problem.splitlines() if line.strip()]
    if len(problem_lines) != 3:
        errors.append(
            f"README problem block has {len(problem_lines)} lines; expected 3"
        )
    for rate in rates.values():
        if rate not in problem:
            errors.append(f"README problem block missing recomputed rate {rate}")
    for phrase in (
        "scripted",
        "does not show",
        "LLM",
        "human annotation",
        "in progress",
    ):
        if phrase not in problem:
            errors.append(f"README problem block missing {phrase!r}")
    try:
        recorded = _between(text, HEADLINE_START, HEADLINE_END).strip()
    except ValueError as exc:
        errors.append(str(exc))
        recorded = ""
    if recorded != block:
        errors.append("README headline block does not match the recomputed result")
    if "Human annotation is not done." not in text:
        errors.append("README does not state that human annotation is not done")
    if "Author-machine path" not in text:
        errors.append("README does not label author-machine paths")
    if "STATUS: WORK-IN-PROGRESS — not A yet" not in text:
        errors.append("README status line missing")
    if "Designed failures: none" not in text:
        errors.append("README must say whether tests fail by design")
    return errors


def check_replay(tasks: list[RecoveryTask], rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if len(tasks) != 40:
        errors.append(f"frozen task count is {len(tasks)}, expected 40")
    if len(rows) != 160:
        errors.append(f"committed trace count is {len(rows)}, expected 160")
    replay = run_recovery_matrix(tasks)["rows"]
    committed = sorted(_row_key(row) for row in rows)
    recomputed = sorted(_row_key(row) for row in replay)
    if committed != recomputed:
        errors.append(
            "committed recovery traces do not match a replay on the frozen tasks"
        )
    if not retry_like_only_on_tool_error(rows):
        errors.append(
            "retry-only and rollback do not succeed only on tool_error in the traces"
        )
    summary = _load_json(TRACE_FILE)["by_policy"]
    rates = aggregate_rates(rows)
    for policy, rate in rates.items():
        recorded = _format_rate(float(summary[policy]["success_rate"]))
        if recorded != rate:
            errors.append(
                f"artifact summary for {policy} is {recorded}, rows aggregate to {rate}"
            )
    return errors


def _corpus_text() -> str:
    chunks: list[str] = []
    for pattern in CORPUS_GLOBS:
        for path in ROOT.glob(pattern):
            if path.is_file() and "docs/" not in path.as_posix():
                chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def _derived_ratios() -> set[str]:
    ratios: set[str] = set()
    for path in ROOT.glob("artifacts/**/*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        stack: list[Any] = [payload]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                successes = item.get("successes")
                denominator = item.get("cases", item.get("tasks"))
                if isinstance(successes, int) and isinstance(denominator, int):
                    ratios.add(f"{successes}/{denominator}")
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
    return ratios


def _page_tokens() -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for pattern in PAGE_GLOBS:
        for path in ROOT.glob(pattern):
            if path.suffix == ".css" or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            # Drop version strings and hex hashes before tokenizing.
            stripped = VERSION_RE.sub(" ", text)
            stripped = re.sub(r"\b[a-f0-9]{7,64}\b", " ", stripped)
            for match in NUMBER_RE.finditer(stripped):
                token = re.sub(r"\s+", "", match.group())
                found.append((path.relative_to(ROOT).as_posix(), token))
    return found


def check_pages(block: str, rates: dict[str, str]) -> list[str]:
    errors: list[str] = []
    allowed = _corpus_text()
    allowed_ratios = _derived_ratios()
    for line in block.splitlines():
        allowed += "\n" + line
    for path, token in _page_tokens():
        if token in allowed or token in allowed_ratios:
            continue
        errors.append(f"{path} shows {token}, which is not in a committed evidence file")
    home = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    evidence = (ROOT / "docs/assets/evidence.js").read_text(encoding="utf-8")
    control = (ROOT / "docs/control/index.html").read_text(encoding="utf-8")
    paper = (ROOT / "docs/paper/index.html").read_text(encoding="utf-8")
    combined_pages = "\n".join(
        path.read_text(encoding="utf-8")
        for pattern in PAGE_GLOBS
        for path in ROOT.glob(pattern)
        if path.is_file()
    )
    for banned in BANNED_PAGE_CLAIMS:
        if banned in combined_pages:
            errors.append(f"pages still show unsupported claim {banned!r}")
    for rate in (rates["replan"], rates["retry-only"]):
        if rate not in home or rate not in paper:
            errors.append(f"home or paper page missing headline rate {rate}")
    if "Scripted-policy" not in home:
        errors.append("home page missing Scripted-policy label")
    if "5/5 replan" in evidence:
        errors.append("evidence.js still labels replan as 5/5")
    if f"replan {rates['replan']}" not in evidence:
        errors.append("evidence.js P2 metric does not quote the recomputed replan rate")
    p2 = control.split('data-package="P2"', 1)[-1].split('data-package="P3"', 1)[0]
    if f">{rates['replan']}<" not in p2:
        errors.append("control page P2 reading is not the recomputed replan rate")
    release = RELEASE_COMMIT_FILE.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    if release not in evidence or release not in paper:
        errors.append("pages cite a release commit that is not in release-commit.txt")
    completed = subprocess.run(
        ["git", "rev-parse", "v0.1.0^{commit}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        tagged = completed.stdout.strip()
        if tagged != release:
            errors.append(
                f"release-commit.txt is {release}, v0.1.0 tag is {tagged}"
            )
    return errors


def check_boundaries() -> list[str]:
    errors: list[str] = []
    status = (ROOT / "PORTFOLIO-STATUS.md").read_text(encoding="utf-8")
    if "Author-machine path" not in status:
        errors.append("PORTFOLIO-STATUS.md does not label the author-machine path")
    if "/home/liuzewen/projects/longrun-agi-20261027" not in status:
        errors.append("author-machine path string missing from PORTFOLIO-STATUS.md")
    failure_modes = ROOT / "FAILURE_MODES.md"
    if not failure_modes.is_file():
        errors.append("FAILURE_MODES.md missing")
    else:
        modes = failure_modes.read_text(encoding="utf-8")
        for heading in (
            "Scripted-baseline ceiling",
            "Task-family leakage",
            "Bootstrap assumptions",
            "Poisoned-memory design limits",
        ):
            if heading not in modes:
                errors.append(f"FAILURE_MODES.md missing {heading}")
    annotation_dirs = [
        path
        for path in ROOT.glob("annotations/**")
        if path.is_file()
    ]
    if annotation_dirs:
        errors.append("annotation files are committed; the not-done claim would be false")
    return errors


def collect_errors() -> list[str]:
    errors: list[str] = []
    try:
        tasks = load_frozen_tasks()
        rows = load_committed_rows()
        errors.extend(check_replay(tasks, rows))
        rates = aggregate_rates(rows)
        canonical = recompute_clear_canonical_sha256()
        block = headline_block(rates, canonical)
        errors.extend(check_readme(block, rates))
        errors.extend(check_pages(block, rates))
        errors.extend(check_boundaries())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
    return errors


def main() -> int:
    errors = collect_errors()
    if errors:
        print("headline check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    rows = load_committed_rows()
    rates = aggregate_rates(rows)
    digest = hashlib.sha256(TRACE_FILE.read_bytes()).hexdigest()
    print("headline check passed")
    print(f"result: recovery-matrix-v1 scripted controllers")
    print(f"traces: {TRACE_FILE.relative_to(ROOT)} sha256={digest}")
    print(
        "rates: "
        + ", ".join(f"{policy}={rate}" for policy, rate in rates.items())
    )
    print("does not show: LLM recovery, external validity, human annotation")
    print("model_gate: hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
