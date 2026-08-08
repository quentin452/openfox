# ai21labs/AI21-Jamba2-3B

|                                     |                                                                                                                                                                    |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| LM Studio key                       | `ai21labs_ai21-jamba2-3b`                                                                                                                                          |
| Hugging Face (weights)              | <https://huggingface.co/ai21labs/AI21-Jamba2-3B> — safetensors only, so `lms get` cannot take it directly                                                           |
| Hugging Face (**the one to pull**)  | <https://huggingface.co/bartowski/ai21labs_AI21-Jamba2-3B-GGUF>, Q4_K_M                                                                                            |
| Parameters                          | 3 B                                                                                                                                                                |
| Architecture                        | `jamba` — hybrid SSM/Transformer (Mamba + attention)                                                                                                               |
| Licence                             | Apache 2.0                                                                                                                                                         |
| Quantisation                        | Q4_K_M                                                                                                                                                             |
| On disk                             | 1.86 GB                                                                                                                                                            |
| Tool use                            | documented by AI21 — its own quickstart passes `--enable-auto-tool-choice --tool-call-parser hermes`. **Claimed, not yet measured here** (probe F does that)        |

## The load, and it is the finding

```
declared 262 144   loaded 262 144   VRAM 3 342 MiB of 12 288
```

**It is the first model measured on this box whose loaded window equals its declared one.** Every
other one is fitted down to the card without saying so — `qwen3.5-9b` declares 262 144 and loads
126 720 or 128 000, `lfm2.5-2.6b` declares and loads 128 000 but comprehends 84 707 of it.

**And it was predicted from `config.json` before anything was downloaded**, which is the method worth
keeping: 28 layers with `attn_layer_period: 14` and `attn_layer_offset: 7` means **two attention
layers**, `num_key_value_heads: 1`, `head_dim` 128. So the KV cache costs
`2 layers × 2 (K,V) × 1 head × 128 × 2 bytes = 1 KiB per token` — **0.26 GiB at 262 144 tokens**.
Measured total: 1.86 GB of weights and 3 342 MiB resident, which is that prediction plus overhead.

**This is the architecture point, not a parameter-count point.** A dense 3 B at 256k needs tens of
GiB of cache; this needs a quarter of one, because only two of its layers have attention to cache.
Compare `Qwen/Qwen3-30B-A3B-Instruct-2507`, which is *also* 256k native and 3.3 B active: its 48
dense layers cost ~96 KiB/token — 24 GiB at 256k, against 12 GB of VRAM and 31 GB of RAM. Fewer
active parameters does not mean a smaller cache.

## How to reproduce the load

```bash
lms get https://huggingface.co/bartowski/ai21labs_AI21-Jamba2-3B-GGUF --gguf -y
./lmstudio.sh load ai21labs_ai21-jamba2-3b 262144 max
```

**`lms get` rejects the `repo@QUANT` form for this name** — it answers `invalid_string` on
`target.name`. The full Hugging Face URL works. That is a second way this command fails after the
safetensors-only case already recorded in the kit.

## What is NOT measured yet

**Everything that matters after "it loads".** A window that loads is not a window the model can
reason across — `lfm2.5-2.6b` loads 128 000 and comprehends 66.2 % of it, and that gap is exactly
what probe G exists to find. Nothing here says whether this model tool-calls, whether it answers
honestly, or whether it can do arithmetic.

In order: **probe G** (`find-window.py`), because a 256k window that comprehends 40k changes what
this model is for; then **A–K**, where **F is the one to watch** since tool use is claimed and
`zai-org/glm-4.6v-flash` is the precedent for a model that cannot complete a tool-calling turn at
all; then **L**, the arithmetic.
