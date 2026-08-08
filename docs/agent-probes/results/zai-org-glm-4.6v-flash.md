# zai-org/glm-4.6v-flash

| | |
|---|---|
| LM Studio key | `zai-org/glm-4.6v-flash` |
| Hugging Face | <https://huggingface.co/zai-org/glm-4.6v-flash> — derived from the model key, **not verified by fetching it** |
| Parameters | 9.4 B |
| Architecture | `glm4` |
| Quantisation | Q4_K_M |
| On disk | 7.95 GB |
| Type | vision-language (`vlm`) |

## Loading, on the machine in `README.md`

| | |
|---|---|
| Declared context | 131 072 |
| **Loaded context** | **131 072** — the only one of the three that loads what it declares |
| Weights estimate | 7.41 GiB, confidence LOW |
| Measured VRAM, default load | **10 651 MiB** of 12 288 |
| `--gpu max` at ctx 131 072 | **refuses to load**: `llama-server ... exited before becoming healthy` |

**The last row is the finding.** Full GPU offload at its declared context does not fit on a 12 GB
card, so the run below was partially offloaded. Its latencies are therefore not comparable with
qwen's second run, and the comparison this file's author first drew — "glm is 3× faster" — was
comparing configurations rather than models.

## Probe G — the usable window

| Depth | Result | Time | Real prompt tokens |
|---|---|---|---|
| 8 000 | PASS | 28.4 s | 7 347 |
| 32 000 | PASS | 102.5 s | 29 707 |
| 64 000 | PASS | 191.9 s | 60 104 |
| 128 000 | **PASS** | 505.9 s | **122 333** |
| 200 000 | HTTP 400, 2.0 s | — | never read |

**Usable window: 122 333 tokens**, of 131 072 declared and loaded — 93.3 %.

Within **351 tokens** of qwen's usable window, from a completely different declared figure. Two
models whose settings pages disagree by 131 072 tokens end up a rounding error apart in practice,
which is the whole argument for measuring rather than reading.

## Other probes

Not yet run. See `../PROBES.md`.
