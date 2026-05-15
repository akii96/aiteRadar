"""Deterministic AITER PR classifier."""

from __future__ import annotations

import importlib.resources
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


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
    reasons: list[MatchReason]

    def to_dict(self) -> dict[str, Any]:
        return {
            "labels": self.labels,
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
        rules_path = importlib.resources.files("aiteradar").joinpath("rules.yaml")
        with rules_path.open("r", encoding="utf-8") as handle:
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

        text = "\n".join([_string_value(pr, "title"), _string_value(pr, "body")])
        self._apply_rules(text, self.text_rules, source="text", labels=labels, reasons=reasons)

        self._add_fallbacks(labels, reasons)

        return Classification(
            labels=sorted(labels),
            reasons=sorted(reasons, key=lambda item: (item.label, item.source, item.rule, item.matched)),
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

    def _add_fallbacks(self, labels: set[str], reasons: list[MatchReason]) -> None:
        required_prefixes = {
            "model:": "model:unknown",
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
