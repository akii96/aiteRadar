# Cross-Repo Analysis Guide

This guide shows how to use InfeRadar's normalized labels to compare work across inference engine repositories.

## The 10-Year-Old Inference Guru Use Case

**Goal**: Pass changelog JSONs to an LLM to identify uplift opportunities.

**Example Questions**:
1. "What MoE optimizations did vllm do that we should port to ATOM?"
2. "Which repos support RDNA4, and what did they implement?"
3. "Show me all DeepSeek-V4 work - who's ahead?"
4. "What quantization methods does each repo support?"

## How Normalized Labels Help

### ✅ **Consistent Naming**
- All repos use `component:moe` (not moe-layer, mixture-of-experts, etc.)
- All repos use `hardware:amd` (not rocm, hip, amd-gpu, etc.)
- Makes it trivial to query across repos

### ✅ **Hierarchical Structure**
```
hardware:amd               # Find ALL AMD work
├── arch:gfx942           # Drill down to MI300
├── arch:gfx950           # Drill down to MI355X
└── arch:gfx1201          # Drill down to RDNA4
```

### ✅ **Cross-Repo Diff**
```python
# Pseudo-code for LLM analysis
vllm_labels = set(extract_labels("vllm.json"))
sglang_labels = set(extract_labels("sglang.json"))

vllm_only = vllm_labels - sglang_labels
sglang_only = sglang_labels - vllm_labels

# Outputs:
# vllm_only: ["component:kv-connector", "hardware:cpu"]
# sglang_only: ["hardware:npu", "hardware:mlx", "component:disaggregation"]
```

## Example Analyses

### 1. Hardware Platform Coverage

**Query**: "Which repos support which hardware?"

**Expected Output**:
```
hardware:nvidia  → vllm ✓, sglang ✓, ATOM ✗, AITER ✗
hardware:amd     → vllm ✓, sglang ✓, ATOM ✓, AITER ✓
hardware:intel   → vllm ✓, sglang ✓, ATOM ✗, AITER ✗
hardware:cpu     → vllm ✓, sglang ✗, ATOM ✗, AITER ✗
hardware:npu     → vllm ✗, sglang ✓, ATOM ✗, AITER ✗
hardware:mlx     → vllm ✗, sglang ✓, ATOM ✗, AITER ✗
```

**Insight**: vllm has the broadest hardware support. SGLang is unique with NPU/MLX. ATOM/AITER are AMD-focused.

### 2. Model Family Support

**Query**: "Which repos are working on DeepSeek-V4?"

**LLM Prompt**:
```
Filter all PRs with label:model:deepseek
Group by repo
Show component breakdown
```

**Expected Output**:
```
DeepSeek Work Distribution:
- vllm: 45 PRs
  └─ Top components: moe (15), attention (12), quantization (8)
- sglang: 67 PRs  
  └─ Top components: moe (20), mla (18), quantization (15)
- ATOM: 23 PRs
  └─ Top components: mla (12), plugin (5), quantization (4)
- AITER: 31 PRs
  └─ Top components: mla (15), moe (10), kernels (6)
```

**Insight**: SGLang has most DeepSeek work. ATOM/AITER focus on MLA (DeepSeek-specific attention).

### 3. Component Feature Gaps

**Query**: "What does vllm have that ATOM doesn't?"

**LLM Analysis**:
```
vllm-only features (components):
- component:kv-connector (disaggregation via Ray)
- component:tool-calling (function calling)
- component:speculative (medusa, eagle, ngram)
- hardware:cpu (CPU inference support)

ATOM-only features (components):
- component:plugin (vLLM plugin integration)
- component:mesh (ATOM mesh networking)
- backend:aiter (AITER kernel integration)
- backend:gluon (Gluon kernels)
```

**Insight**: vllm is more feature-complete (speculative, tool-calling). ATOM has unique ROCm integration depth.

### 4. Performance Optimization Comparison

**Query**: "What perf optimizations were made to MoE across repos?"

**LLM Prompt**:
```
Filter: component:moe AND type:perf
Group by: repo
Extract: PR titles and techniques
```

**Expected Output**:
```
MoE Performance Work:
- vllm: 
  - "Replace torch.compile pack with fused Triton kernels" (backend:triton)
  - "Add linear backend argument for kernel selection" (component:kernels)
- sglang:
  - "reuse prev-layer output for FP4 routed MoE" (component:quantization)
  - "Migrate flashinfer_cutedsl to MoeRunner" (backend:flashinfer)
- ATOM:
  - "DSV4 fusion phase2" (backend:triton)
```

**Insight**: vllm focuses on Triton fusion, sglang on quantization reuse, ATOM on Triton DSV4-specific.

### 5. AMD Architecture Coverage

**Query**: "What's the RDNA4 (gfx1201) support status?"

**LLM Prompt**:
```
Filter: arch:gfx1201
Group by: repo, component
```

**Expected Output**:
```
RDNA4 (gfx1201) Work:
- ATOM: 2 PRs
  └─ "Mistral-3 + Qwen3-8B-FP8 on RDNA4 via native triton attention"
  └─ component:attention, backend:triton
- Others: 0 PRs
```

**Insight**: ATOM is pioneering RDNA4 support. Uplift opportunity for AITER/sglang.

## Label Quality Checklist

When adding new rules, ask:

1. **Is this label name consistent with other repos?** 
   - ✅ Use `hardware:amd` (not `rocm`, `hip`)
   - ✅ Use `component:quantization` (not `quant-layer`, `compression`)

2. **Is this concept shared across repos?**
   - ✅ Yes → Use common label from taxonomy
   - ❌ No → Use repo-specific label (e.g., `component:kv-connector` for vllm)

3. **Can an LLM easily compare this?**
   - ✅ "All repos with `model:deepseek`"
   - ❌ vllm uses `deepseek-v4`, sglang uses `dsv4`, ATOM uses `ds_v4`

4. **Does it help identify uplift opportunities?**
   - ✅ "`component:speculative` in vllm but not ATOM → port?"
   - ❌ "`file-touched:server.py`" → too generic, not actionable

## Tips for LLM Analysis

When passing changelogs to an LLM for comparison:

1. **Aggregate by time period** - Compare same week across repos
2. **Focus on component/hardware/model** - Ignore state labels (merged/open_pr)
3. **Count frequency** - High PR count = active area
4. **Look for gaps** - "This repo has X, others don't"
5. **Track trends** - "X repo added Y feature this week"

## Future Enhancements

Possible improvements to label system:

1. **Technique tags** - `technique:fusion`, `technique:autotune`, `technique:compilation`
2. **Priority levels** - `priority:p0`, `priority:p1` based on PR urgency
3. **Complexity** - `complexity:simple`, `complexity:large` for effort estimation
4. **Dependencies** - `depends:pytorch`, `depends:triton-3.0` for dependency tracking
