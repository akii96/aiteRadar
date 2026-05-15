from __future__ import annotations

import json
from pathlib import Path

from aiteradar.classifier import Classifier


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_prs.json"


def test_model_config_gets_model_kernel_and_tuning_labels() -> None:
    classifier = Classifier.from_package_rules()
    pr = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))[0]

    result = classifier.classify_pr(pr)

    assert "model:deepseek" in result.labels
    assert "kernel:gemm" in result.labels
    assert "type:tuning-config" in result.labels
    assert "backend:triton" in result.labels
    assert "arch:gfx950" in result.labels


def test_cpp_cache_kernel_gets_multi_labels() -> None:
    classifier = Classifier.from_package_rules()
    pr = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))[1]

    result = classifier.classify_pr(pr)

    assert "model:deepseek" in result.labels
    assert "backend:hip-cpp" in result.labels
    assert "backend:python-api" in result.labels
    assert "kernel:cache" in result.labels
    assert "kernel:quant" in result.labels
    assert "type:new-kernel" in result.labels
    assert result.reasons


def test_gluon_attention_kernel_gets_backend_arch_and_kernel_labels() -> None:
    classifier = Classifier.from_package_rules()
    pr = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))[2]

    result = classifier.classify_pr(pr)

    assert "backend:gluon" in result.labels
    assert "backend:triton" in result.labels
    assert "kernel:attention" in result.labels
    assert "kernel:quant" in result.labels
    assert "arch:gfx950" in result.labels
    assert "arch:gfx1250" in result.labels
    assert "type:new-kernel" in result.labels


def test_model_aliases_are_deterministic() -> None:
    classifier = Classifier.from_package_rules()
    cases = {
        "DeepSeek-V3.2 tuned GEMM": "model:deepseek",
        "minimax_m25 fp4 fmoe": "model:minimax",
        "kimik2 i4 moe": "model:kimi",
        "gpt-oss swiglu A4W4 path": "model:gpt-oss",
    }

    for title, expected in cases.items():
        result = classifier.classify_pr({"title": title, "body": "", "files": []})
        assert expected in result.labels


def test_fallback_labels_keep_unmatched_prs_visible() -> None:
    classifier = Classifier.from_package_rules()

    result = classifier.classify_pr({"title": "chore", "body": "", "files": [{"filename": "misc/file.txt"}]})

    assert result.labels == ["kernel:misc", "model:unknown", "type:misc"]
    assert {reason.source for reason in result.reasons} == {"fallback"}
