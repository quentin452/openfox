# Results

One file per model. Each records what the model is, what it costs to load, and how it answered every
probe — pass, fail, refusal or timeout, with the number that says so.

**Every file names the machine it was measured on.** A context window and a latency are properties
of a model *on a card*, not of the model: the same weights on a bigger card take a longer window,
and the same window with the KV cache in system RAM takes six times longer to fill. A result with no
machine beside it is a number somebody will misread later.

## The machine, for every result in this directory

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 3060, 12 288 MiB |
| Runtime | LM Studio, OpenAI-compatible server on `:1234` |
| Client | `probe_g` ladder over `../ground-truth.sh` needles, `temperature 0` |
| Date | 2026-08-08 |

## Why there is one file per model and no folder per card

The obvious filing is a directory per GPU — `rtx-3060-12gb/` — and it is the wrong split, because
**the card decides only half of what is in these files and the two halves have different shapes.**

* *What the card decides* is one row: does it load, at what offload, how much VRAM, what context
  LM Studio managed to fit. Card-dependent, config-dependent, and it changes when either moves.
* *What the model decides* is everything else — does it invent a file, can it say "I have not read
  that", does it notice a truncated list. **A bigger card does not make a model honest.**

A folder per card would put the second half in a place that implies it depends on the first. So the
split is inside each file — a *Loading, on the machine in `README.md`* table, then the probes — and
the machine is named once, here. If a second machine ever measures the same model, the honest shape
is **a second row in that file's loading table**, not a second copy of the file under another
directory. Two copies of a model's honesty results, one per card, would be two things that must
agree forever and nothing checking that they do.

`lfm2.5-2.6b` is the case that makes the argument concrete: it is the only model here whose window
is limited by the *model* rather than by the card. Filed under `rtx-3060-12gb/`, its most useful
finding would sit in a folder whose name says the opposite of what it means.

## How to reproduce one

```bash
../lmstudio.sh status                                  # what is loaded, at what context
../lmstudio.sh load <model> <ctx> max                  # load it deliberately
../find-window.py --model <model> --note "--gpu max"   # probe G, bisected to ±500 tokens
../ground-truth.sh /path/to/target/repo ./key          # the key the other probes need
../run-probe.py --repo /path/to/target/repo --model <model> "<probe text>"
```

## What the four runs taught, in one line each

- **Declared is not loaded.** Two of three models declare 262 144 and load 126 720 — LM Studio fits
  the KV cache to the VRAM it has, silently.
- **Where the KV cache lives is worth 6x.** Same model, same window, one toggle.
- **A timeout is not a limit.** One model's "window" was my client's patience.
- **A window can be the model's fault rather than the card's.** `lfm2.5-2.6b` loads all 128 000 of
  its declared context with 10 GiB of VRAM to spare and still loses the marker at 84 707.
- **Grading the wrong field reports a window of zero.** A thinking model answers in
  `reasoning_content`; a runner reading only `content` scores it wrong at every depth.
