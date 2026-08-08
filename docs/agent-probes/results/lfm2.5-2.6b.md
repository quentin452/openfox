# lfm2.5-2.6b

| | |
|---|---|
| LM Studio key | `lfm2.5-2.6b` |
| Hugging Face | <https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF> — **the GGUF repo, and that is the one that matters**: `lms get` on `LiquidAI/LFM2.5-2.6B` fails with *no download options available*, because that repo is safetensors only |
| Parameters | 2.7 B |
| Architecture | `lfm2` |
| Quantisation | Q5_K_M |
| On disk | 1.94 GB |
| Type | thinking — it answers in `reasoning_content`, and `content` can be empty |

## Loading, on the machine in `README.md`

| | |
|---|---|
| Declared context | 128 000 |
| **Loaded context** | **128 000** — the second model here to load what it declares |
| Offload | `--gpu max` at ctx 128 000, which **fits**: 1.81 GiB resident |
| Room left | ~10 GiB of 12 288 MiB free. The only model measured here that leaves the card mostly empty |

## Probe G — the usable window, bisected

Measured with `../find-window.py`, which starts at the loaded ceiling and halves what is left
unknown. Nine requests, about four minutes.

| Depth (chars) | Verdict | Real prompt tokens | Time |
|---|---|---|---|
| 501 760 | WRONG | 115 582 | 14.4 s |
| 250 880 | PASS | 57 461 | 3.2 s |
| 376 320 | WRONG | 86 512 | 34.9 s |
| 313 600 | PASS | 71 977 | 30.3 s |
| 344 960 | PASS | 79 254 | 31.4 s |
| 360 640 | PASS | 82 883 | 34.2 s |
| **368 480** | **PASS** | **84 707** | 37.2 s |
| 372 400 | WRONG | 85 600 | 37.4 s |
| 370 440 | WRONG | 85 163 | 37.4 s |

**Usable window: 84 707 tokens**, of 128 000 declared and loaded — **66.2 %**.

**It is the first model here whose window is limited by the model rather than by the card.** The
other three were capped by what LM Studio could fit; this one loads its whole declared context with
10 GiB to spare and still stops finding the marker at two thirds of it. A bigger card would not move
this number.

**The failure mode at the edge is a corrupted marker, not a refusal.** At 85 163 tokens it answered
`NEEDLE-902` — the right shape, the wrong string, said with no hedge. At 85 600 it quoted a filler
line instead. Nothing ever returned HTTP 400, because the text always fitted: this is a comprehension
limit, and §G's distinction between a refusal and a failure is exactly what tells the two apart.

## What running this cost the kit, recorded because it was nearly a wrong number

The first version of `find-window.py` asked for 64 output tokens and graded only `content`. This
model spends its output on reasoning before it answers, so every rung came back with an empty
`content`, `finish_reason: length`, and the marker sitting unread in `reasoning_content` — scored
`WRONG` at **every** depth, which would have recorded a usable window of zero for a model that was
answering correctly. The script now grades both fields, treats an exhausted output cap as its own
verdict rather than as a failure, and asks for 1 024 tokens.

## Other probes

Not yet run. See `../PROBES.md`.
