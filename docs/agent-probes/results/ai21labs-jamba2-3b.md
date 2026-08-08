# ai21labs/AI21-Jamba2-3B

|                                    |                                                                                                                                                              |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| LM Studio key                      | `ai21labs_ai21-jamba2-3b`                                                                                                                                    |
| Hugging Face (weights)             | <https://huggingface.co/ai21labs/AI21-Jamba2-3B> — safetensors only, so `lms get` cannot take it directly                                                    |
| Hugging Face (**the one to pull**) | <https://huggingface.co/bartowski/ai21labs_AI21-Jamba2-3B-GGUF>, Q4_K_M                                                                                      |
| Parameters                         | 3 B                                                                                                                                                          |
| Architecture                       | `jamba` — hybrid SSM/Transformer (Mamba + attention)                                                                                                         |
| Licence                            | Apache 2.0                                                                                                                                                   |
| Quantisation                       | Q4_K_M                                                                                                                                                       |
| On disk                            | 1.86 GB                                                                                                                                                      |
| Tool use                           | documented by AI21 — its own quickstart passes `--enable-auto-tool-choice --tool-call-parser hermes`. **Claimed, not yet measured here** (probe F does that) |

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
Compare `Qwen/Qwen3-30B-A3B-Instruct-2507`, which is _also_ 256k native and 3.3 B active: its 48
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

## Probe G — the usable window, 2026-08-08

**262 055 real tokens of the 262 144 loaded. 100.0 %, and the gap is 89 tokens.**

```
  1 027 604 chars  REFUSED      never read     0.8s  HTTP 400
    513 802 chars  PASS      137 111 tokens   51.9s
    770 703 chars  PASS      206 037 tokens   85.7s
    899 153 chars  PASS      241 193 tokens  107.4s
    963 378 chars  PASS      258 995 tokens  119.5s
    995 491 chars  REFUSED      never read     1.2s  HTTP 400
    979 434 chars  REFUSED      never read     0.9s  HTTP 400
    971 406 chars  PASS      261 226 tokens  119.1s
    975 420 chars  REFUSED      never read     0.9s  HTTP 400
    973 413 chars  PASS      261 779 tokens  119.6s
    974 416 chars  PASS      262 055 tokens  119.6s
```

**What makes this different from `lfm2.5-2.6b` is not the number, it is the FAILURE MODE.** Every
failure here is `REFUSED` — HTTP 400 in under a second, the server declining the request before the
model saw a character. Not one depth came back `WRONG`. So the edge measured is the **server's
context limit**, and the model was never found to have a comprehension limit below it: it read
every depth it was allowed to read. `lfm2.5-2.6b` fails the other way — the server accepts, the
model answers, and the answer is wrong from 84 707 tokens up. That is the distinction probe G's four
outcomes exist to keep apart (`PROBES.md` §G), and it is the first time the two have been seen side
by side on this box.

**What this does NOT say.** Probe G is a needle: a marker planted in filler and asked for back.
Finding it at 262 055 tokens proves the model **read** that far, not that it can reason across what
it read. Retrieval is the cheapest thing a long window can do — every hybrid architecture is at its
best here, because a marker survives a state-space pass that a comparison between two distant facts
might not. The probes that ask for more are A–K.

Cost: about two minutes per request at full depth, 119.6 s for the passing run — prompt processing,
not generation. Eleven requests, bisected from the ceiling.

## What is NOT measured yet

**Everything except the window.** Nothing here says whether this model tool-calls, whether it
answers honestly, or whether it can do arithmetic.

Next: **A–K**, where **F is the one to watch** since tool use is claimed by AI21 and
`zai-org/glm-4.6v-flash` is the precedent for a model that cannot complete a tool-calling turn at
all; then **L**, the arithmetic.
