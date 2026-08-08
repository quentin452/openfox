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

## Probe G — 118 431 tokens, the whole loaded context

```
gpt-oss-nano: declared 131,072, LOADED 131,072  [Q4_K_M, --gpu max, widened grader, cap 4096]

    513,802 chars  MANGLED   118431 tokens   107.7s  'NEDEL‑1‑513802'

usable window: 118,431 real tokens — the whole loaded context. Nothing to bisect.
```

The ceiling rung passed on the first request, so the bisect had no space left to search.

**The prior this file carried was REFUTED, and that is worth more than the number.** 131 072 is YaRN
**32× from a 4096 native window**, and every note here said to expect the declared-versus-usable gap
that produces. There is none. An extension that aggressive holding across its whole range is the
first counter-example this kit has to *"a big declared window is a claim"*.

### The first run said 28.1 %, and the grader was wrong twice in one day

| Run | Grader | Output cap | Usable |
| --- | --- | --- | --- |
| first | exact, then case-insensitive | 1024 | **36 807** — 28.1 % |
| second | + index/depth pair, dashes folded | 4096 | **118 431** — all of it |

**A 3.2× correction, from two independent defects that both under-measure:**

* **The word `NEEDLE` was being graded, and it carries no information.** What identifies a needle is
  `-{index}-{chars}`, and `chars` is the prompt's own length — a model cannot produce it without
  having read the line. This model returned `NEDEL‑1‑513802`: right index, right depth, letters
  dropped from the constant, and **ASCII hyphens replaced by U+2011 NON-BREAKING HYPHEN** (confirmed
  by codepoint, not by eye). Graded whole that is WRONG; graded on what it means it is a read at the
  ceiling. `MANGLED` had been widened this same morning for the *case* version of exactly this, on
  `ai21-jamba-reasoning-3b`, and it cost 24 % there.
* **Four rungs of ten came back `TRUNCATED` at a 1024 cap** — *"output cap reached before it said
  anything"*. `gpt-oss` reasons before answering, so it spent the cap on thinking. That verdict
  measures the runner, which is why the script keeps it apart from the model's failures; the fix is
  `--max-tokens 4096`, and the setting is recorded here beside the number rather than assumed.

### It reads correctly and transcribes badly, and that is a flag for A–K

Every wrong-looking answer had the **right index and the right depth**. What it damaged was the
constant it was asked to echo. **A model that corrupts a string it has just read will corrupt a
filename, a commit hash or a line number**, and none of those has an index/depth pair to fall back
on. Probe G cannot see that as a failure; A–K is where it would show.

## What is still NOT measured

A–K. Under the selection rule — a smaller context that is good beats a bigger one that hallucinates —
it has to beat `qwen3.5-9b-deepseek-v4-flash`, which is measured at 99.7 % of 128 000 and **10 of
11**. On window they are now comparable (118 431 against 127 563) and nano is the faster of the two
by construction, since it fits entirely on the card. **The whole question is behaviour.**

**What this file establishes:** it FITS, it is FAST, and it READS its whole window. Three questions
that could each have killed it, and it survived all three.

## Probe M — writing `.catz`, graded by a compiler, 2026-08-08

**The probe A–K could not be: nothing is graded by eye.** The answer is a `.catz` file written into
the CatzEngine corpus, walked by `catz-gates::roundtrip`, and taken out again. The brief is
`FORMAT.md` §7 read out of the document plus the palette's ink names — **9 078 characters, about
2 269 tokens**, which is the whole context this task needs and a thirtieth of what the model loads.

| Tier | | |
| --- | --- | --- |
| parses | **ok** | the lexer accepted it |
| resolves | **ok** | every word it wrote exists in the declaration table |
| reads | **NO** | `argument 2 is not a group — a point is written in parentheses, as (x,y,z,r)` |
| prints | **ok** | byte-identical on the round trip — the format's founding contract (§1.4) |
| gated | NO | the corpus does not pass with it in |

**Three of five, failing on one rule of shape.** It wrote `spine (0,0,0,1) stone`: one parenthesised
point where a spine is a CHAIN and needs two or more, and a bare `stone` where the ink is a named
argument. An earlier run put `ink=stone` on its own line instead. Everything else was right —
the three headers, the exact subject line, two-space indent, solids nested under their `part`, and
**no `ground`**, which is the one semantic rule that separates a `prop` from a `creature`.

**What this says about the plan:** the model is one or two rules away from producing corpus-legal
content with no training at all, on a task whose entire specification fits in 2 269 tokens. That is a
small gap, and `catzc` labels every attempt — accepted files are positive examples, refused ones come
with the diagnostic that says why. The scarcest ingredient in a fine-tune is already free here.

### The harness graded itself wrong twice before it graded the model

Recorded because it is the same defect this kit keeps finding, committed by the kit:

1. **It asked whether a marker string was ABSENT and called that success**, so a refusal it did not
   anticipate was reported as three passing tiers.
2. **It then searched a 1 200-character TAIL** of the test output for that marker, with the
   diagnostic sitting above the cut — which is probe K's own failure mode, in the grader.

The fix was to stop guessing the engine's prose and read the **name of the failing test**, which the
engine owns and changes with itself. Three graders in one day — `MANGLED` for case, `MANGLED` for
dashes, and this — all narrow in the same direction: **scoring the wording instead of the thing.**
