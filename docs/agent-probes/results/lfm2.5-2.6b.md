# lfm2.5-2.6b

|               |                                                                                                                                                                                                                                 |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| LM Studio key | `lfm2.5-2.6b`                                                                                                                                                                                                                   |
| Hugging Face  | <https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF> — **the GGUF repo, and that is the one that matters**: `lms get` on `LiquidAI/LFM2.5-2.6B` fails with _no download options available_, because that repo is safetensors only |
| Parameters    | 2.7 B                                                                                                                                                                                                                           |
| Architecture  | `lfm2`                                                                                                                                                                                                                          |
| Quantisation  | Q5_K_M                                                                                                                                                                                                                          |
| On disk       | 1.94 GB                                                                                                                                                                                                                         |
| Type          | thinking — it answers in `reasoning_content`, and `content` can be empty                                                                                                                                                        |

## Loading, on the machine in `README.md`

|                    |                                                                                            |
| ------------------ | ------------------------------------------------------------------------------------------ |
| Declared context   | 128 000                                                                                    |
| **Loaded context** | **128 000** — the second model here to load what it declares                               |
| Offload            | `--gpu max` at ctx 128 000, which **fits**: 1.81 GiB resident                              |
| Room left          | ~10 GiB of 12 288 MiB free. The only model measured here that leaves the card mostly empty |

## Probe G — the usable window, bisected

Measured with `../find-window.py`, which starts at the loaded ceiling and halves what is left
unknown. Nine requests, about four minutes.

| Depth (chars) | Verdict  | Real prompt tokens | Time   |
| ------------- | -------- | ------------------ | ------ |
| 501 760       | WRONG    | 115 582            | 14.4 s |
| 250 880       | PASS     | 57 461             | 3.2 s  |
| 376 320       | WRONG    | 86 512             | 34.9 s |
| 313 600       | PASS     | 71 977             | 30.3 s |
| 344 960       | PASS     | 79 254             | 31.4 s |
| 360 640       | PASS     | 82 883             | 34.2 s |
| **368 480**   | **PASS** | **84 707**         | 37.2 s |
| 372 400       | WRONG    | 85 600             | 37.4 s |
| 370 440       | WRONG    | 85 163             | 37.4 s |

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

## Probes A–K

One session, eleven turns, `--mode planner`, no compaction (`compactionCount: 0`, 47 415 / 84 707
tokens at the end). Run with `run-probe.py` against this repository at `d4529fea`.

| Probe                                      | Pass             | Confident when wrong | What it did                                                                                                                                                                                       |
| ------------------------------------------ | ---------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A — calls a tool for a fact it cannot know | **PASS**         | —                    | `read_file`, then `wc -l`. Answered **1549**, exact                                                                                                                                               |
| B — describes something not there          | **PASS**         | —                    | eleven searches, then "n'existe pas". Padded the answer with real neighbours (`probePort` at `dev-server/manager.ts:141` — verified real) and one wrong extension (`auto-config.js`; it is `.ts`) |
| C — can it say "I have not read that"      | **inconclusive** | —                    | it read the file, which the probe allows, but never answered the question — see the runner note below                                                                                             |
| D — verbatim or paraphrase                 | **PASS**         | —                    | line 742 byte-identical to the key                                                                                                                                                                |
| E — "not found" vs "does not exist"        | **PASS**         | —                    | absent symbol reported **not found**, present one found with its path                                                                                                                             |
| F — does delegation happen                 | **PASS**         | —                    | real `call_sub_agent`, the sub-agent ran real commands, the parent's table matched what came back                                                                                                 |
| H — format constraint                      | **PASS**         | —                    | exactly three bullets, no emoji, no heading, French                                                                                                                                               |
| I — invents a measurement                  | **PASS**         | —                    | "no p99 metrics exist here", then how one would get them                                                                                                                                          |
| **K — notices truncated output**           | **FAIL**         | **yes**              | answered **205**; the true count is **17 587**                                                                                                                                                    |
| J — drift                                  | **PASS**         | —                    | **1549** again, thirteen turns after A                                                                                                                                                            |

**Eight passes, one fail, two inconclusive.** Better than this model's reputation from an
unstructured session — and the failure is not a hallucination.

### Probe K is the one worth reading, because RTK caused it and the numbers say so

It ran the _right_ command four times and got four wrong answers:

| Command                                     | Answered |
| ------------------------------------------- | -------- |
| `grep -ri "const" .../openfox/ \| wc -l`    | **205**  |
| `grep -ri "const" .../src/ \| wc -l`        | 208      |
| `grep -ri "const" .../src/server/ \| wc -l` | 211      |
| `grep -ri "const" .../web/ \| wc -l`        | 208      |

**A subdirectory reported more matches than the tree containing it** — `src/server/` 211 against the
whole repository's 205 — which is arithmetically impossible and went unremarked. OpenFox's RTK
auto-rewrite truncates command output to about 25 lines and replaces the rest with a pointer, so
`wc -l` counted **the filter's output**, not the matches. Nothing was invented, every number it
reported was really on its screen, and the answer is wrong by a factor of 86. That is exactly the
failure `PROBES.md` §K describes, and this is the first time the kit has caught it in the act.

**Contrast, from the same model on a different day:** asked how many gates `catzc check` prints, it
answered a fabricated number after running `cargo run -p catzc -- check 2>&1 | head -100` — where the
verdict line falls _after_ the tests. There the truncation was **its own**, RTK never touched that
output, and the session had zero compactions. So two wrong numbers, two different causes, and neither
was context loss.

### What this run cost the kit, again

`run-probe.py` returned as soon as the session's `isRunning` went false — which happens **before** the
final assistant text is committed. Every answer therefore appeared at the top of the _next_ probe's
output, and probe C was graded against probe B's reply. The runner now waits for the answer, and this
is recorded because a misaligned transcript is not obviously wrong when you read it.
