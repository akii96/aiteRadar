"""Deterministic AITER PR classifier."""

from __future__ import annotations

import importlib.resources
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

MAX_REASONS_PER_LABEL = 3


@dataclass(frozen=True)
class MatchReason:
    label: str
    source: str
    rule: str
    pattern: str
    matched: str

    def to_dict(self) -> dict[str, str]:
        return {
            "label": self.label,
            "source": self.source,
            "rule": self.rule,
            "pattern": self.pattern,
            "matched": self.matched,
        }


@dataclass(frozen=True)
class CompiledRule:
    name: str
    pattern: str
    labels: tuple[str, ...]
    regex: re.Pattern[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CompiledRule":
        pattern = str(payload["pattern"])
        labels = tuple(str(label) for label in payload.get("labels", []))
        return cls(
            name=str(payload["name"]),
            pattern=pattern,
            labels=labels,
            regex=re.compile(pattern, re.IGNORECASE),
        )


@dataclass(frozen=True)
class Classification:
    labels: list[str]
    primary_labels: list[str]
    auxiliary_labels: list[str]
    reasons: list[MatchReason]

    def to_dict(self) -> dict[str, Any]:
        return {
            "labels": self.labels,
            "primary_labels": self.primary_labels,
            "auxiliary_labels": self.auxiliary_labels,
            "reasons": [reason.to_dict() for reason in self.reasons],
        }


class Classifier:
    def __init__(
        self,
        rule_version: int,
        path_rules: list[CompiledRule],
        text_rules: list[CompiledRule],
        fallback_labels: list[str],
    ) -> None:
        self.rule_version = rule_version
        self.path_rules = path_rules
        self.text_rules = text_rules
        self.fallback_labels = fallback_labels

    @classmethod
    def from_package_rules(cls) -> "Classifier":
        # Default to AITER rules in the rules/ directory
        rules_path = Path(__file__).parent.parent.parent / "rules" / "rules-aiter.yaml"
        with open(rules_path, "r", encoding="utf-8") as handle:
            return cls.from_yaml_text(handle.read())

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> "Classifier":
        return cls.from_yaml_text(Path(path).read_text(encoding="utf-8"))

    @classmethod
    def from_yaml_text(cls, text: str) -> "Classifier":
        payload = yaml.safe_load(text)
        return cls(
            rule_version=int(payload["version"]),
            path_rules=[CompiledRule.from_dict(rule) for rule in payload.get("path_rules", [])],
            text_rules=[CompiledRule.from_dict(rule) for rule in payload.get("text_rules", [])],
            fallback_labels=[str(label) for label in payload.get("fallback_labels", [])],
        )

    def classify_pr(self, pr: Any) -> Classification:
        """Classify a PR-like object with title/body/files attributes or keys."""

        labels: set[str] = set()
        reasons: list[MatchReason] = []

        for filename in _filenames(pr):
            self._apply_rules(
                filename,
                self.path_rules,
                source="path",
                labels=labels,
                reasons=reasons,
            )

        title = _string_value(pr, "title")
        self._apply_rules(title, self.text_rules, source="title", labels=labels, reasons=reasons)
        self._add_state_label(pr, labels, reasons)

        self._add_fallbacks(labels, reasons)
        primary_labels, auxiliary_labels = split_primary_auxiliary_labels(labels)

        return Classification(
            labels=sorted(labels),
            primary_labels=primary_labels,
            auxiliary_labels=auxiliary_labels,
            reasons=_dedupe_and_cap_reasons(reasons),
        )

    def _apply_rules(
        self,
        value: str,
        rules: list[CompiledRule],
        source: str,
        labels: set[str],
        reasons: list[MatchReason],
    ) -> None:
        for rule in rules:
            match = rule.regex.search(value)
            if not match:
                continue
            matched = match.group(0)
            for label in rule.labels:
                labels.add(label)
                reasons.append(
                    MatchReason(
                        label=label,
                        source=source,
                        rule=rule.name,
                        pattern=rule.pattern,
                        matched=matched,
                    )
                )

    def _add_state_label(self, pr: Any, labels: set[str], reasons: list[MatchReason]) -> None:
        state = _string_value(pr, "state")
        if state not in {"merged", "open_pr"}:
            return
        labels.add(state)
        reasons.append(
            MatchReason(
                label=state,
                source="state",
                rule="pull-request-state",
                pattern="state",
                matched=state,
            )
        )

    def _add_fallbacks(self, labels: set[str], reasons: list[MatchReason]) -> None:
        required_prefixes = {
            "model:": "model:general",
            "type:": "type:misc",
            "kernel:": "kernel:misc",
        }
        for prefix, fallback in required_prefixes.items():
            if not any(label.startswith(prefix) for label in labels):
                labels.add(fallback)
                reasons.append(
                    MatchReason(
                        label=fallback,
                        source="fallback",
                        rule="fallback",
                        pattern=f"no {prefix[:-1]} label matched",
                        matched="",
                    )
                )


AUXILIARY_LABELS = {"backend:python-api", "type:tests"}


def split_primary_auxiliary_labels(labels: set[str]) -> tuple[list[str], list[str]]:
    auxiliary = {label for label in labels if label in AUXILIARY_LABELS}
    primary = set(labels) - auxiliary
    return sorted(primary), sorted(auxiliary)


def _dedupe_and_cap_reasons(reasons: list[MatchReason]) -> list[MatchReason]:
    sorted_reasons = sorted(reasons, key=lambda item: (item.label, item.source, item.rule, item.matched))
    seen: set[tuple[str, str, str, str]] = set()
    counts: dict[str, int] = {}
    capped: list[MatchReason] = []
    for reason in sorted_reasons:
        key = (reason.label, reason.source, reason.rule, reason.matched)
        if key in seen:
            continue
        seen.add(key)
        if counts.get(reason.label, 0) >= MAX_REASONS_PER_LABEL:
            continue
        counts[reason.label] = counts.get(reason.label, 0) + 1
        capped.append(reason)
    return capped


def _filenames(pr: Any) -> list[str]:
    files = _value(pr, "files") or []
    names: list[str] = []
    for file_item in files:
        if isinstance(file_item, dict):
            filename = str(file_item.get("filename") or "")
        else:
            filename = str(getattr(file_item, "filename", ""))
        if filename:
            names.append(filename)
    return names


def _string_value(pr: Any, key: str) -> str:
    value = _value(pr, key)
    return "" if value is None else str(value)


def _value(pr: Any, key: str) -> Any:
    if isinstance(pr, dict):
        return pr.get(key)
    return getattr(pr, key, None)
