from __future__ import annotations

import json
from pathlib import Path

from inferadar.classifier import Classifier


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_prs.json"


def test_model_config_gets_model_kernel_and_tuning_labels() -> None:
    classifier = Classifier.from_package_rules()
    pr = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))[0]

    result = classifier.classify_pr(pr)

    assert "model:deepseek" in result.labels
    assert "kernel:gemm" in result.labels
    assert "type:tuning-config" in result.labels
    assert "backend:triton" in result.labels
    assert "arch:gfx950" not in result.labels


def test_cpp_cache_kernel_gets_multi_labels() -> None:
    classifier = Classifier.from_package_rules()
    pr = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))[1]

    result = classifier.classify_pr(pr)

    assert "model:deepseek" in result.labels
    assert "backend:hip-cpp" in result.labels
    assert "backend:python-api" in result.labels
    assert "backend:python-api" in result.auxiliary_labels
    assert "backend:python-api" not in result.primary_labels
    assert "kernel:cache" in result.labels
    assert "kernel:quant" not in result.labels
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

    assert result.labels == ["kernel:misc", "model:general", "type:misc"]
    assert result.primary_labels == result.labels
    assert result.auxiliary_labels == []
    assert {reason.source for reason in result.reasons} == {"fallback"}


def test_pr_body_is_not_scanned_for_labels() -> None:
    classifier = Classifier.from_package_rules()

    result = classifier.classify_pr(
        {
            "title": "chore",
            "body": "DeepSeek MiniMax Kimi GEMM MoE Triton tests docs release",
            "files": [{"filename": "misc/file.txt"}],
        }
    )

    assert result.labels == ["kernel:misc", "model:general", "type:misc"]


def test_reasons_are_deduped_and_capped_per_label() -> None:
    classifier = Classifier.from_package_rules()
    pr = {
        "title": "Add fp8 quant kernel",
        "body": "",
        "files": [
            {"filename": f"aiter/ops/triton/quant/fp8_quant_{idx}.py"}
            for idx in range(10)
        ],
    }

    result = classifier.classify_pr(pr)
    quant_reasons = [reason for reason in result.reasons if reason.label == "kernel:quant"]

    assert "kernel:quant" in result.labels
    assert len(quant_reasons) <= 3
