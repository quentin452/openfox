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

## ⛔ It cannot complete a tool-calling turn, so the other probes have no answer

**Measured 2026-08-08.** Asked for a fact about a file — probe A, the simplest thing the kit does —
it emits the **same tool call over and over until `max_tokens`**, and OpenFox never dispatches any of
them.

| Where | What happened |
|---|---|
| OpenFox, builder mode, probe A | **63** queued tool-call fragments — `read_file` ×30, `run_command` ×30 — none dispatched. Killed at 12 min |
| OpenFox, planner mode, a work request | **25** × `call_sub_agent`, none dispatched, 600 s client timeout |
| LM Studio direct, one tool, `temperature 0` and `0.7`, 8 runs | **3 of 8** returned the same `read_file` 6–10× and stopped at `max_tokens`. The other 5 returned exactly one |
| `repeat_penalty 1.1` | no effect — one of the looping runs had it on |
| **Control: `qwen3.5-9b-deepseek-v4-flash`, same request, 4 runs** | **4/4 exactly one call.** So this is the model, not the harness and not the tool schema |

**What this costs the measurement, said plainly:** probes A–F and H–K are graded on what the agent
does with a tool, and this model's tool calls do not arrive. Its window is the best of the three
measured here and it is unusable as an agent until either the loop stops or a consumer dedupes
identical calls. **Nothing is recorded below as a pass or a fail** — a probe that never ran is not a
probe the model failed, which is the same distinction §G draws between a refusal, a failure and a
timeout.

Two mitigations exist and neither has been applied here: capping `defaultMaxTokens` so a looped turn
ends in seconds rather than hanging, and dedup of identical consecutive tool calls in the consumer.
The second is a change to OpenFox itself.

## Other probes

Not run, and see the section above for why — not for lack of trying. See `../PROBES.md`.
