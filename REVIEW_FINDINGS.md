# Label System Review - Actionable Fixes

## Subagent Review Summary

The subagent found **28 issues** categorized by priority. Here's the action plan:

---

## 🔴 HIGH PRIORITY - Cross-Repo Comparison Blockers

These issues **break cross-repo queries**. Must fix to enable "10-year-old guru" use case.

### 1. Standardize Hardware Labels ⚠️ CRITICAL
**Problem:**
- vLLM uses `hardware:amd-rocm`
- SGLang uses `hardware:amd`
- ATOM uses `hardware:mi300`, `hardware:mi355x`, `hardware:rdna4`
- AITER uses `hardware:mi300`, `hardware:mi355x`, `hardware:rdna4`, `hardware:mi450`

**Impact:** Query "show all AMD work" returns incomplete results.

**Fix:**
- ALL repos use `hardware:amd` (not amd-rocm)
- ATOM/AITER: Remove `hardware:mi300/mi355x/rdna4/mi450`
- ATOM/AITER: Use `arch:gfx942` + `hardware:amd` instead

**Files to change:**
- `rules/rules-vllm.yaml` - Change `hardware:amd-rocm` → `hardware:amd`
- `rules/rules-atom.yaml` - Remove hardware:mi*/rdna4, keep arch:gfx*
- `rules/rules-aiter.yaml` - Remove hardware:mi*/rdna4, keep arch:gfx*

---

### 2. AITER Must Add Component Labels ⚠️ CRITICAL
**Problem:**
- AITER uses `kernel:moe`, `kernel:attention`, etc.
- Other repos use `component:moe`, `component:attention`
- Cross-repo query for "component:moe" misses all AITER PRs

**Fix:** AITER rules should add BOTH labels:
```yaml
# Before:
labels: [kernel:moe]

# After:
labels: [component:moe, kernel:moe]
```

**Files to change:**
- `rules/rules-aiter.yaml` - Add component:* alongside all kernel:* labels

---

### 3. Standardize Frontend Labels
**Problem:**
- vLLM uses `component:frontend-api`
- SGLang uses `component:frontend`
- ATOM uses `component:serving`

**Fix:** All use `component:frontend`

**Files to change:**
- `rules/rules-vllm.yaml` - `frontend-api` → `frontend`
- `rules/rules-atom.yaml` - `serving` → `frontend`

---

### 4. Fix Speculative Decoding Label
**Problem:**
- Taxonomy says `component:speculative`
- All repos use `component:speculative-decode`

**Fix:** Choose one. Recommend keeping `speculative-decode` (more descriptive).

**Files to change:**
- `LABEL_TAXONOMY.md` - Update line 34: `component:speculative` → `component:speculative-decode`

---

### 5. Add Word Boundaries to Patterns
**Problem:**
- Pattern `'expert'` matches "experience", "expert", "export"
- Pattern `'moe'` matches standalone, good
- Pattern `'oob'` matches "booby", "rebook"

**Fix:** Add `\b` word boundaries:
```yaml
# Before:
pattern: 'moe|expert|fused_moe'

# After:
pattern: '\bmoe\b|\bexpert\b|fused_moe'
```

**Files to change:**
- `rules/rules-vllm.yaml` - Lines 28, 103
- `rules/rules-sglang.yaml` - Lines 27, 103
- `rules/rules-atom.yaml` - Lines 37, 111
- `rules/rules-aiter.yaml` - Lines 49, 151

---

## 🟡 MEDIUM PRIORITY - Completeness Issues

These improve label coverage but don't break queries.

### 6. Add Missing Components to Each Repo

**vLLM missing:**
- `component:lora` (SGLang/ATOM have it)
- `component:scheduler` (SGLang has it)
- `component:structured-output` (SGLang has it)

**SGLang missing:**
- `component:kv-cache` (vLLM has it)
- `component:tool-calling` (vLLM has it)

**ATOM missing:**
- `component:kv-cache` (vLLM has it)
- `component:scheduler` (SGLang has it)
- `component:structured-output` (SGLang has it)
- `component:tool-calling` (vLLM has it)
- `component:multimodal` (vLLM/SGLang have it)

**AITER missing:**
- Convert `kernel:cache` → also add `component:kv-cache`
- Add `component:multimodal` if applicable

---

### 7. Add Missing Model Labels

Many repos missing labels for model families they likely support:
- vLLM: Add mixtral, glm, minimax, kimi, gpt-oss
- SGLang: Add mixtral, kimi, gpt-oss
- ATOM: Add gemma, mixtral
- AITER: Add gemma

---

### 8. Add Missing Backend Labels

- vLLM: Add `backend:cuda`
- SGLang/ATOM/AITER: Add `backend:hip`

---

### 9. Improve Model Detection Patterns

**DeepSeek pattern improvements:**
```yaml
# Before:
pattern: '\b(deepseek|dsv4|dsv3|ds.v4|ds.v3)\b'

# Better:
pattern: '\b(deepseek|ds[-_. ]?v[34]|dsv[34]|deepseek[-_]?r1|dsr1)\b'
```

**Quantization pattern improvements:**
```yaml
# Before:
pattern: 'quant|fp8|fp4|int4|int8|w8a8|w4a16|awq|gptq|compressed'

# Better:
pattern: '\bquant|\bfp[48]\b|\bint[48]\b|\bw\d+a\d+\b|\bawq\b|\bgptq\b|compressed'
```

---

## 🟢 LOW PRIORITY - Enhancements

Nice-to-haves that improve usability but aren't blocking.

### 10. Add Glossary to LABEL_TAXONOMY.md

```markdown
## Glossary for Non-Experts

- **MLA**: Multi-Latent Attention (DeepSeek's efficient attention mechanism)
- **MoE**: Mixture of Experts (uses different models for different inputs)
- **KV Cache**: Key-Value cache (stores past tokens for faster generation)
- **LoRA**: Low-Rank Adaptation (efficient fine-tuning method)
- **CK**: Composable Kernel (AMD's kernel library)
- **Triton**: OpenAI's GPU programming language
- **FlashInfer**: Fast attention kernel library
```

---

### 11-13. Future Enhancements

- **Priority labels** - `priority:critical`, `priority:high`, `priority:normal`
- **Complexity labels** - `complexity:small`, `complexity:medium`, `complexity:large`
- **Impact labels** - `impact:major-perf`, `impact:moderate-perf`, `impact:minor-perf`
- **Dependency labels** - `requires:pytorch-2.5`, `requires:triton-3.0`, `requires:rocm-6.3`

---

## 📋 Implementation Plan

### Phase 1: Critical Fixes (Do Now!)
1. Fix hardware label consistency (Issue #1)
2. Add component labels to AITER (Issue #2)
3. Standardize frontend labels (Issue #3)
4. Fix speculative label in taxonomy (Issue #4)
5. Add word boundaries to patterns (Issue #5)

**Time estimate:** ~30 minutes
**Impact:** Unblocks ALL cross-repo comparison queries

### Phase 2: Completeness (Do Soon)
6. Add missing components (Issue #6)
7. Add missing models (Issue #7)
8. Add missing backends (Issue #8)
9. Improve patterns (Issue #9)

**Time estimate:** ~1 hour
**Impact:** Increases label coverage from ~60% → ~90%

### Phase 3: Polish (Do Later)
10. Add glossary (Issue #10)
11-13. Add enhancement labels (Issues #11-13)

**Time estimate:** ~30 minutes
**Impact:** Better documentation and future-proofing

---

## Recommendation

**Do Phase 1 now** to fix critical cross-repo comparison issues. Without these fixes, the "10-year-old guru" use case is broken.

**Do Phase 2 when convenient** to improve coverage. The system works but misses some PRs.

**Skip Phase 3 for now** - These are nice-to-haves that can be added as the project matures.

---

## What Changed Since Last Iteration?

The subagent found we were **75% there** but had critical consistency issues that would break cross-repo queries. The normalized taxonomy is good, but implementation has drift.

**Key insight:** Having a taxonomy document doesn't help if repos don't follow it strictly!
