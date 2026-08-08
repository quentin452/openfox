# cybertruck32489/Jamba-Reasoning-3B-Agent-v1

**The name is the only place the word "agent" appears.** Its model card is the auto-generated
template — every field `[More Information Needed]`, no licence, no `base_model` — so the only way to
learn what was trained was to run it. That is what this file records.

| | |
| --- | --- |
| LM Studio key | `jamba-reasoning-3b-agent-v1` |
| GGUF | <https://huggingface.co/cybertruck32489/Jamba-Reasoning-3B-Agent-v1-gguf>, **Q4_K_M 1.84 GB** |
| Base | `ai21labs/AI21-Jamba-Reasoning-3B` (by architecture and size; the card does not say) |
| Declared / loaded | 262 144 / **262 144**, 1.71 GiB resident |
| Measured | 2026-08-08, RTX 3060, same probes and same quant tier as the baseline |

## The finding in one line

**Someone trained long context and wrote "Agent" on the box.** The usable window goes up **5.2×**
against its base; every agent behaviour the probes test is unchanged or worse.

## Probe G — 85 452 usable tokens against the base's 16 403

```
  1,027,604 chars  REFUSED      never read     0.8s  HTTP 400
    513,802 chars  WRONG     137 152 tokens   53.7s  [reasoning] restated the question
    256,901 chars  PASS       68 226 tokens   24.4s  'The marker string is: NEEDLE-3-256901'
    321,126 chars  PASS       85 452 tokens   40.4s
    323,133 chars  WRONG      86 003 tokens   33.3s  '<|im_start|>marker|<|im_start|/>'
usable window: 85,452 real tokens of 262,144 loaded — 32.6 %
```

**This is not an artefact of the `MANGLED` fix.** That verdict can only turn a WRONG into a read,
never the reverse, and the base's hard ceiling was ~33.7 k tokens — it answered `>` above that. 85 452
is out of the base's reach under any grading. **So this repository is not a renamed checkpoint:
something was trained, and it was the window.**

## A–K — 1 pass, 8 fail. The base scored 2.

| Probe | Base `ai21-jamba-reasoning-3b` | **Agent-v1** |
|---|---|---|
| A — count lines | FAIL, answered 35 | **FAIL** — read the file, answered **4**. The truth is 1 549 |
| B — absent file | FAIL, echoed the system prompt | **FAIL** — emitted raw `<\|im_start\|>` and no summary |
| C — is it in context | FAIL, investigated then said yes | **FAIL, and worse** — never answered, and **fabricated a `<tool_response>` block** with an invented exit code |
| D — verbatim quote | FAIL, empty response | **FAIL** — dumped a different part of the file (`broadcastAll`), never line 742, then `>` |
| E — found vs exists | FAIL, said both exist | **FAIL** — called `web_search` (no output), and its thinking ends planning "a conclusion summarizing that both functions exist". No answer committed |
| F — delegation | FAIL, fetched an invented URL | **FAIL** — no `call_sub_agent`, 20 s of thinking, empty content |
| H — three bullets | pass (numbered) | **pass** — real bullets, no emoji, no heading |
| I — invent a p99 | **pass** — refused | **FAIL** — invented `/Logs/server.log` and a `raw.githubusercontent.com/co-l/openfox` URL, then repeated one identical `read_file` **nine times**. Never refused, never answered |
| K — count with a filter | FAIL, no answer | **FAIL** — answered `<\|im_start\|>` |

## Two pathologies worth keeping, because neither is in the base

**It fabricates tool results.** In probe C it wrote, in its own output, at the exact shape the
harness produces:

```
<tool_response>
{ "type": "error", "message": "Error: Command exited with code 1", "exitCode": 1 }
</tool_response>
```

That result never existed. **A harness that parses tool results out of assistant text rather than
from its own dispatcher can be fed forged evidence by the model** — worth checking in OpenFox
independently of any model.

**It leaks ChatML control tokens** — `<|im_start|>`, `</|im_start>`, `<|im_start|>marker|<|im_start|/>`
— in G, B and K. That is a model trained under one chat template and packaged with another, and it
is not cosmetic: **it hung the harness for over twelve minutes on probe C**, with OpenFox reporting
`isRunning: true` while LM Studio sat IDLE and the assistant message was empty.

## Methodology note, stated rather than hidden

G, A and B ran at the kit's default `--timeout 900`. After the twelve-minute hang was diagnosed,
**C–K were re-run at `--timeout 240`**: a probe that would have answered between four and fifteen
minutes is scored here as a hang. The baseline answered every probe in under 100 s except A, so the
exposure is small — but the two runs are not timed identically.

## What it is for

**Nothing this box needs.** For a window that is actually read, `ai21labs_ai21-jamba2-3b` reads
262 055 tokens — three times this one — and scores the same on agency. This model is a
demonstration that **long-context training and agent training are different purchases**, which is
the useful thing it produced.
