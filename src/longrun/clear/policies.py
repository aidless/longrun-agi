from __future__ import annotations

import json
import re
from pathlib import PurePosixPath
from typing import Any

from .models import Action, Observation, Op


class PolicyError(RuntimeError):
    pass


RULE_PATTERN = re.compile(
    r"<RULE_JSON>\s*(\{.*?\})\s*</RULE_JSON>",
    re.DOTALL,
)


def parse_rule(content: str) -> tuple[str, dict[str, str]]:
    match = RULE_PATTERN.search(content)
    if not match:
        raise PolicyError("docs/SPEC.md does not contain a RULE_JSON block")
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise PolicyError(f"invalid RULE_JSON: {exc}") from exc
    mode = payload.get("mode")
    mapping = payload.get("map")
    if mode not in {"extension", "prefix", "suffix"}:
        raise PolicyError(f"unsupported routing mode: {mode!r}")
    if not isinstance(mapping, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in mapping.items()
    ):
        raise PolicyError("RULE_JSON map must be a string-to-string object")
    return mode, mapping


def parse_cached_rule(
    content: str,
) -> tuple[str, dict[str, str], str, float]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise PolicyError(f"invalid cached rule JSON: {exc}") from exc
    value = payload.get("value", payload)
    mode = value.get("mode")
    mapping = value.get("map")
    if mode not in {"extension", "prefix", "suffix"}:
        raise PolicyError(f"unsupported cached routing mode: {mode!r}")
    if not isinstance(mapping, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in mapping.items()
    ):
        raise PolicyError("cached RULE_JSON map must be a string-to-string object")
    source = payload.get("source", "")
    trust = payload.get("trust", 0.0)
    if not isinstance(source, str):
        raise PolicyError("cached rule source must be a string")
    if not isinstance(trust, (int, float)) or not 0.0 <= float(trust) <= 1.0:
        raise PolicyError("cached rule trust must be in [0, 1]")
    return mode, mapping, source, float(trust)


def destination_for(path: str, mode: str, mapping: dict[str, str]) -> str:
    basename = PurePosixPath(path).name
    if mode == "extension":
        key = PurePosixPath(basename).suffix
    elif mode == "prefix":
        key = basename.split("__", 1)[0]
    elif mode == "suffix":
        stem = PurePosixPath(basename).stem
        key = stem.rpartition("__")[2]
    else:
        raise PolicyError(f"unsupported mode: {mode}")
    if key not in mapping:
        raise PolicyError(f"no route for {key!r} in {path!r}")
    return f"sorted/{mapping[key]}/{basename}"


class _SpecPolicyBase:
    name = "spec-policy"

    def __init__(
        self,
        *,
        retain_rule: bool = False,
        retry_on_error: bool = True,
        source_dir: str = "inbox",
    ) -> None:
        self.retain_rule = retain_rule
        self.retry_on_error = retry_on_error
        self.source_dir = source_dir
        self.mode: str | None = None
        self.mapping: dict[str, str] = {}
        self.pending: list[str] = []
        self.current_move: Action | None = None
        self.phase = "start"

    def reset(self) -> None:
        if not self.retain_rule:
            self.mode = None
            self.mapping = {}
        self.pending = []
        self.current_move = None
        self.phase = "start"

    def _initial_phase(self) -> str:
        if self.retain_rule and self.mode is not None and self.mapping:
            return "listing"
        return "reading"

    def act(self, observation: Observation) -> Action:
        if self.phase == "start":
            self.phase = self._initial_phase()
            if self.phase == "listing":
                return Action(Op.LIST, path=self.source_dir)
            return Action(Op.READ, path="docs/SPEC.md")

        if self.phase == "reading":
            if not observation.ok:
                return self._retry_or_fail(Action(Op.READ, path="docs/SPEC.md"))
            self.mode, self.mapping = parse_rule(str(observation.value))
            self.phase = "listing"
            return Action(Op.LIST, path=self.source_dir)

        if self.phase == "listing":
            if not observation.ok:
                return self._retry_or_fail(Action(Op.LIST, path=self.source_dir))
            values = observation.value or []
            self.pending = sorted(
                str(path)
                for path in values
                if str(path).startswith(f"{self.source_dir}/")
            )
            if not self.pending:
                self.phase = "finishing"
                return Action(Op.FINISH)
            self.phase = "moving"
            self.current_move = self._next_move()
            return self.current_move

        if self.phase == "moving":
            if not observation.ok:
                if self.current_move is None:
                    raise PolicyError("move failed without a retryable action")
                return self._retry_or_fail(self.current_move)
            if self.pending:
                self.current_move = self._next_move()
                return self.current_move
            self.phase = "finishing"
            return Action(Op.FINISH)

        if self.phase == "finishing":
            return Action(Op.FINISH)

        raise PolicyError(f"invalid policy phase: {self.phase}")

    def _retry_or_fail(self, action: Action) -> Action:
        if self.retry_on_error:
            return action
        raise PolicyError("policy aborted after a tool failure")

    def _next_move(self) -> Action:
        if self.mode is None:
            raise PolicyError("routing mode is not initialized")
        path = self.pending.pop(0)
        destination = destination_for(path, self.mode, self.mapping)
        return Action(Op.MOVE, src=path, dst=destination)


class ReactiveSpecPolicy(_SpecPolicyBase):
    """Read the current specification for every task."""

    name = "reactive-spec"


class StickySpecPolicy(_SpecPolicyBase):
    """Reuse the first routing rule learned within a family."""

    name = "sticky-spec"

    def __init__(self, *, source_dir: str = "inbox") -> None:
        super().__init__(
            retain_rule=True,
            retry_on_error=True,
            source_dir=source_dir,
        )


class ConfigurableSpecPolicy(_SpecPolicyBase):
    """Factorial-policy switch for attribution experiments."""

    def __init__(
        self,
        *,
        retain_rule: bool,
        retry_on_error: bool,
        source_dir: str = "inbox",
    ) -> None:
        super().__init__(
            retain_rule=retain_rule,
            retry_on_error=retry_on_error,
            source_dir=source_dir,
        )
        self.name = (
            f"configurable-retain={int(retain_rule)}-"
            f"retry={int(retry_on_error)}"
        )


class MemorySpecPolicy(_SpecPolicyBase):
    """Use a cached routing note, optionally enforcing provenance."""

    def __init__(
        self,
        *,
        trusted_memory: bool,
        retry_on_error: bool = True,
        source_dir: str = "inbox",
    ) -> None:
        super().__init__(
            retain_rule=False,
            retry_on_error=retry_on_error,
            source_dir=source_dir,
        )
        self.trusted_memory = trusted_memory
        self.name = f"memory-{'provenance' if trusted_memory else 'naive'}"

    def _initial_phase(self) -> str:
        return "memory-reading"

    def act(self, observation: Observation) -> Action:
        if self.phase == "start":
            self.phase = self._initial_phase()
            return Action(Op.READ, path="memory/routing-note.json")

        if self.phase == "memory-reading":
            if not observation.ok:
                return self._retry_or_fail(
                    Action(Op.READ, path="memory/routing-note.json")
                )
            mode, mapping, source, trust = parse_cached_rule(
                str(observation.value)
            )
            if self.trusted_memory and (
                source != "docs/SPEC.md" or trust < 0.5
            ):
                self.phase = "reading"
                return Action(Op.READ, path="docs/SPEC.md")
            self.mode = mode
            self.mapping = mapping
            self.phase = "listing"
            return Action(Op.LIST, path="inbox")

        return super().act(observation)
