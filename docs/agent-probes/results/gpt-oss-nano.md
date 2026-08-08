# `squ11z1/gpt-oss-nano` — 12 experts of `gpt-oss-20b`'s 32

**Machine:** RTX 3060, 12 GB; 31 GB system RAM; LM Studio. **Measured 2026-08-08.**

## What it is, read from `config.json` rather than from its card

Its `config.json` is **identical to `openai/gpt-oss-20b`'s on every field that decides cost** — 24
layers alternating `sliding_attention` / `full_attention`, `hidden_size` 2880, `head_dim` 64, 8 KV
heads, 4 experts per token, `max_position_embeddings` 131 072, YaRN factor 32 from an
`initial_context_length` of 4096 — with exactly two differences:

* `num_local_experts` is **12**, where the parent has 32.
* There is **no `quantization_config`**: the weights are bf16, where the parent ships MXFP4.

The card calls it *"a fine-tuned Mixture of Experts"* and never says pruned. LM Studio labels it
**`12x2.4B`**, which is the same reading arrived at independently. Its own GGUFs are published, so
the usual hunt for a `-GGUF` sibling does not apply: `gpt-oss-9b-q4_k_m.gguf` is 6.83 GB, `q8_0`
9.55 GB, `bf16` 17.95 GB. Card claims no benchmark; its "Limitations" are boilerplate.

## It loads its full declared window, and it is the second model here to do so

```
gpt-oss-nano | loaded ctx 131072 | max ctx 131072   [Q4_K_M, --gpu max]
```

Predicted from the architecture before the download and confirmed by the load. **12 of the 24 layers
are full attention and the other 12 are capped at a 128-token sliding window**, so the cache costs
about **24 KiB/token** — 3.0 GiB at 131 072, against 6.36 GiB of weights. 9.4 GiB on an 11.2 GiB
card, with room left.

`ai21labs_ai21-jamba2-3b` was the first to load its declared window. This is the first to do it at a
size that might be worth using.

## Throughput: three cells, because two would have proved nothing

`PROBES.md` lists *"comparing configurations while claiming to compare models"* among the five ways
this kit has already produced a wrong number. Comparing nano-on-GPU against 20b-spilling changes the
model **and** the placement at once, so a third cell holds the placement fixed and varies only the
model.

Prompt processing and generation are reported apart because they degrade differently: the first is
compute-bound, the second memory-bandwidth-bound, and weights living in system RAM wreck the second
while barely touching the first. One blended figure would hide exactly that.

| Cell | Model | Offload | Loaded ctx | 6 833 prompt tok | 27 114 prompt tok |
| --- | --- | --- | --- | --- | --- |
| **A** | nano 9B | `--gpu max` | 131 072 | ttft 3.34 s · **68.9 tok/s** | ttft 10.94 s · **62.9 tok/s** |
| **B** | nano 9B | `--gpu 0.6` | 32 768 | ttft 7.33 s · **15.8 tok/s** | ttft 22.33 s · **10.7 tok/s** |
| **C** | gpt-oss-20b | `--gpu 0.6` | 32 768 | ttft 8.60 s · **19.1 tok/s** | ttft 24.87 s · **12.7 tok/s** |

**The finding is B against C: the 9 B model in partial offload is SLOWER than the 21 B model in the
same partial offload.** Holding the model constant and moving from full to partial costs **4.4×**
then **5.9×** in generation. Holding the placement constant and doubling the parameter count costs
nothing — the larger model is 20 % faster.

**So it is the spill that costs, not the size.** `gpt-oss-20b` is not slow here because it is a 21 B;
it is slow because this card cannot hold it. On a 16 GB card it would plausibly run at cell A's
numbers, and the verdict against it is *"not on this machine"* rather than *"not this model"*.

**The confound runs against the conclusion, which is why it is reported rather than hidden.** Cell A
was loaded at 131 072 and B and C at 32 768 — A had the *larger* context and is still four times
faster. B against C is matched setting for setting.

**Generation degrades with depth only when weights are off the card**: nano loses 9 % between the two
depths at full offload (68.9 → 62.9) and 32 % at partial (15.8 → 10.7); the 20b loses 33 %.

## `--gpu max` does not degrade gracefully — it dies

Asked for `gpt-oss-20b` at `-c 32768 --gpu max`, LM Studio loaded to **75 %** and then:

```
Error: Engine protocol runtime llama-server for si63e/… exited before becoming healthy.
exitCode=1, signal=null
```

It does not fall back to a partial split. **Partial offload has to be configured**, and the ratio is
a number somebody chooses: `--gpu 0.6` loaded, meaning roughly 14 of 24 layers resident.

## What is NOT measured

Everything about whether it is any good: probe G (its usable window against the 131 072 it loads),
and A–K. **The YaRN prior is poor** — 32× from a 4096 native window is exactly the declared-versus-
usable gap this kit exists to measure — and under the selection rule (a smaller context that is good
beats a bigger one that hallucinates) it has to beat `qwen3.5-9b-deepseek-v4-flash`, which is already
measured at 99.7 % of 128 000 and 10 of 11 on A–K.

**What this file establishes is only that it FITS and that it is fast when it does.** Those are the
two questions that would have killed it, and it survived both.
