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

## How to reproduce one

```bash
../lmstudio.sh status                                  # what is loaded, at what context
../lmstudio.sh load <model> <ctx> max                  # load it deliberately
../ground-truth.sh /path/to/target/repo ./key          # regenerate the needles
# then run the probes in PROBES.md, reading each marker OUT of its needle file
```

## What the three runs taught, in one line each

- **Declared is not loaded.** Two of three models declare 262 144 and load 126 720 — LM Studio fits
  the KV cache to the VRAM it has, silently.
- **Where the KV cache lives is worth 6x.** Same model, same window, one toggle.
- **A timeout is not a limit.** One model's "window" was my client's patience.
