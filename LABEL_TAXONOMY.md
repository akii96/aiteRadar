# InfeRadar Label Taxonomy

This document defines the **normalized label taxonomy** used across all inference engine repositories. The goal is to enable cross-repo comparison and identify uplift opportunities.

## Design Principles

1. **Consistency**: Same label names for same concepts across repos
2. **Hierarchical**: Labels organized by category for easy filtering
3. **Comparable**: Easy to query "what does repo X have that Y doesn't?"
4. **Discoverable**: A 10-year-old should understand what each label means

## Label Categories

### 1. Type (What kind of change?)
- `type:feature` - New functionality
- `type:bugfix` - Bug fixes
- `type:perf` - Performance optimizations
- `type:refactor` - Code restructuring
- `type:docs` - Documentation
- `type:tests` - Test additions/changes
- `type:ci-build` - CI/build system changes
- `type:revert` - Reverts previous changes

### 2. Component (What part of the system?)
Core serving components:
- `component:kernels` - Low-level compute kernels
- `component:attention` - Attention mechanisms (Flash, Paged, etc.)
- `component:moe` - Mixture of Experts
- `component:mla` - Multi-Latent Attention (DeepSeek-specific)
- `component:quantization` - Quantization/compression
- `component:kv-cache` - KV cache management
- `component:scheduler` - Request scheduling
- `component:distributed` - Multi-GPU/distributed inference
- `component:speculative-decode` - Speculative decoding
- `component:multimodal` - Vision/multimodal support

Serving infrastructure:
- `component:frontend` - API/serving layer
- `component:tool-calling` - Function/tool calling support
- `component:structured-output` - Constrained generation (grammar, JSON schema)

Special components:
- `component:lora` - LoRA adapter support
- `component:disaggregation` - Prefill/decode disaggregation (separate processes)
- `component:plugin` - Plugin systems (ATOM/vLLM integration)
- `component:general` - Doesn't fit other categories

### 3. Hardware (What hardware platform?)
- `hardware:nvidia` - NVIDIA GPUs (CUDA)
- `hardware:amd` - AMD GPUs (ROCm/HIP)
- `hardware:intel-xpu` - Intel GPUs (XPU/OneAPI)
- `hardware:cpu` - CPU inference
- `hardware:npu` - NPU (Neural Processing Unit)
- `hardware:musa` - Moore Threads MUSA
- `hardware:mlx` - Apple MLX

Architecture-specific (AMD):
- `arch:gfx942` - MI300/MI308
- `arch:gfx950` - MI355X
- `arch:gfx1201` - RDNA4

### 4. Backend (What compute backend?)
- `backend:triton` - OpenAI Triton
- `backend:cuda` - Native CUDA
- `backend:hip` - AMD HIP
- `backend:flashinfer` - FlashInfer library
- `backend:cutlass` - NVIDIA CUTLASS
- `backend:ck` - AMD Composable Kernel
- `backend:aiter` - AITER kernels
- `backend:gluon` - Gluon (Triton-based)
- `backend:torch-compile` - PyTorch compilation

### 5. Model (Which model families?)
- `model:deepseek` - DeepSeek (V3, V4, R1)
- `model:qwen` - Qwen/Qwen2/Qwen3
- `model:llama` - LLaMA family
- `model:mistral` - Mistral
- `model:mixtral` - Mixtral MoE
- `model:gemma` - Gemma
- `model:glm` - GLM/ChatGLM
- `model:minimax` - MiniMax
- `model:kimi` - Kimi
- `model:gpt-oss` - GPT-OSS/Quark
- `model:general` - Generic/not model-specific

### 6. State (PR status)
- `merged` - PR was merged
- `open_pr` - PR is open/pending

## Cross-Repo Comparison Queries

Examples of useful queries enabled by this taxonomy:

**What hardware does each repo support?**
```
Filter: hardware:*
Compare: Count by repo
```

**DeepSeek work across repos**
```
Filter: model:deepseek
Group by: repo, component
```

**MoE optimization comparison**
```
Filter: component:moe AND type:perf
Compare: Techniques by repo
```

**AMD-specific work**
```
Filter: hardware:amd
Group by: arch:*, component
```

**What's vllm doing that sglang isn't?**
```
vllm labels NOT IN sglang labels
```

## Repo-Specific Extensions

Some repos may have unique components not found elsewhere:
- **vllm**: `component:kv-connector` (for Ray-based disaggregation)
- **sglang**: Better at scheduler/radix-cache
- **ATOM**: `component:mesh`, `component:plugin`

These are kept but should map to common concepts where possible (e.g., kv-connector → disaggregation).

## Glossary for Non-Experts

Technical terms explained for the "10-year-old inference guru":

**Components:**
- **MoE (Mixture of Experts)**: Uses different "expert" neural networks for different inputs instead of one big model
- **MLA (Multi-Latent Attention)**: DeepSeek's memory-efficient attention mechanism  
- **KV Cache**: Stores previous tokens' keys and values so the model doesn't recompute them
- **LoRA (Low-Rank Adaptation)**: Efficient way to fine-tune models by only training small adapter layers
- **Speculative Decoding**: Guesses multiple tokens ahead to speed up generation
- **Quantization**: Reduces number precision (FP32→FP8→INT4) to save memory and speed up inference

**Hardware:**
- **gfx942**: AMD's MI300/MI308 GPU architecture code name
- **gfx950**: AMD's MI355X GPU architecture
- **gfx1201**: AMD's RDNA4 consumer GPU architecture
- **sm80/sm90/sm100**: NVIDIA GPU compute capability (A100/H100/B200)

**Backends:**
- **Triton**: OpenAI's Python-based GPU programming language
- **CK (Composable Kernel)**: AMD's high-performance kernel library
- **FlashInfer**: Fast attention kernel library
- **HIP**: AMD's CUDA-equivalent programming model
- **CUDA**: NVIDIA's GPU programming platform
- **Gluon**: AMD's Triton-based kernel framework

**Models:**
- **DeepSeek-V4/V3**: DeepSeek's latest models with MLA and MoE
- **Qwen**: Alibaba's open-source LLM family
- **LLaMA**: Meta's foundational LLM

**Platforms:**
- **ROCm**: AMD's complete GPU software stack (like CUDA for AMD)
- **OneAPI**: Intel's unified programming model
