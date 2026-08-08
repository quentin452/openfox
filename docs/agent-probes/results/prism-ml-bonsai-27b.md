# prism-ml/bonsai-27b

| | |
|---|---|
| LM Studio key | `prism-ml/bonsai-27b` |
| Hugging Face | <https://huggingface.co/prism-ml/bonsai-27b> — derived from the model key, **not verified by fetching it** |
| Parameters | 27 B |
| Architecture | `qwen35` |
| Quantisation | **Q1_0** |
| On disk | 4.73 GB — a 27 B that fits in less space than the 9 B beside it, which is what Q1 buys and what it costs |
| Type | vision-language (`vlm`) |

## Loading, on the machine in `README.md`

| | |
|---|---|
| Declared context | 262 144 |
| **Loaded context** | **126 720** — auto-fitted, like qwen and unlike glm |
| Weights estimate | 4.41 GiB, confidence LOW |
| Measured VRAM, default load | **6 296 MiB** of 12 288 — the roomiest of the three |

## Probe G — a window that was never found

| Depth | Result | Time | Real prompt tokens |
|---|---|---|---|
| 8 000 | PASS | 99.1 s | 8 290 |
| 32 000 | PASS | 316.8 s | 33 605 |
| 64 000 | **TIMEOUT** | 900.1 s | — |

**Usable window: ≥ 33 605 tokens, upper bound unknown.**

⚠️ **The 64 000 rung is not a failure and not a limit.** The client gave up after fifteen minutes
while the model was still processing. What was measured there is the patience of a script — and
since the loaded context is 126 720, the window is certainly far above where the ladder stopped.

Three times slower than the 9 B at the same depth, on a machine where it uses the *least* VRAM. For
agent work the wall here is throughput, not capacity: at 32 000 tokens of context it costs five
minutes before the first token of an answer.

## Other probes

Not yet run. See `../PROBES.md`. Given the latency above, the honest next step for this model is a
throughput measurement rather than more depth: a model that answers correctly in ten minutes fails
a different requirement than one that answers wrongly in ten seconds.
