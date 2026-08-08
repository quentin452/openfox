# ai21labs/AI21-Jamba-Reasoning-3B

| | |
| --- | --- |
| LM Studio key | `ai21-jamba-reasoning-3b` |
| Hugging Face | <https://huggingface.co/ai21labs/AI21-Jamba-Reasoning-3B-GGUF> — **official GGUF from AI21**, Q4_K_M 1.93 GB |
| Licence | Apache 2.0 (+ Jamba Open Model License) |
| Published | 2025-10-08 |
| Architecture | `jamba` — 28 layers, **26 Mamba / 2 attention**, 20 Q heads / **1 KV head** (MQA), hidden 2560, dense (`num_experts: 1`) |
| Declared / loaded | 262 144 / **262 144**, 1.80 GiB resident |
| Tool use | documented; the chat template carries `tool`, `function`, `thinking`, `reasoning` |

**Its `config.json` is identical to `ai21labs_ai21-jamba2-3b`'s** on every field that decides cost:
28 layers, 2560 hidden, 20 heads, 1 KV head, `attn_layer_period 14`, `attn_layer_offset 7`, one
expert, 262 144. So the pair below differs by **post-training and nothing else that is visible from
the config** — which is what makes the comparison worth writing down. Lineage is not established
here; only that the two are architecturally the same shape.

## Probe G — 7.7 % of what it loads, and the failures are the model's

**Re-run 2026-08-08 with the `MANGLED` grader, `--gpu max`.** This is the measurement; the run below
it is kept because it is what a case-sensitive grader reports.

```
  1,027,604 chars  REFUSED      never read     0.8s  HTTP 400
    513,802 chars  WRONG     137 142 tokens   61.9s  [reasoning] echoed the filler back
    256,901 chars  WRONG      68 216 tokens   33.7s  [reasoning] echoed the filler back
    128,450 chars  WRONG      33 742 tokens   12.1s  '>'
     64,225 chars  MANGLED    16 675 tokens   10.2s  '<needle-5-64225>'
     96,337 chars  WRONG      25 139 tokens   16.4s  '<answer>marker</answer>'
     80,281 chars  WRONG      20 833 tokens   16.7s  [reasoning] restated the task
     72,253 chars  PASS       18 754 tokens   16.3s  [reasoning] restated the task
     76,267 chars  MANGLED    19 783 tokens   10.4s  '<needle-9-76267>'
     78,274 chars  PASS       20 309 tokens   15.8s  [reasoning] restated the task
     79,277 chars  WRONG      20 582 tokens   12.5s  '<answer>marker</answer>'

usable window: 20,309 real tokens of 262,144 loaded — 7.7 %, edge within 500 tokens
```

**The bracket the previous run left has closed, and it closed inside itself.** That run predicted
the honest edge lay between ~16.7 k and ~33.7 k; it is 20 309, and the number moved from 6.3 % to
7.7 % — the direction a grader fix can only move it. **`MANGLED` earned its place twice in one run**,
at 16 675 and again at 19 783: both were the marker returned lowercased inside the angle brackets it
had seen around the filler, and both would have scored WRONG before.

**Two distinct wrong answers sit either side of the edge, and they are not the same failure.**
Below it the model restates the task in `reasoning` and answers correctly; above it, at 20 582 and
25 139, it answers the literal string `<answer>marker</answer>` — it has stopped retrieving a marker
and started echoing the SHAPE of the question. That is worth more than the percentage: the failure
is not a truncated context, it is the instruction surviving while the content does not.

**This remains the opposite failure mode to its architectural twin, and that is still the finding.**
`ai21labs_ai21-jamba2-3b` never answered wrong: every failure above its edge was the server refusing,
and it retrieved at 262 055 tokens — 100 %. This one is accepted by the server, answers, and is wrong
from about 20.5 k tokens up. Same `config.json` on every field that decides cost, same loaded window,
**a thirteenth of the usable one.**

### The run that predates `MANGLED`, kept for what it shows about grading

```
     64,225 chars  WRONG      16 675 tokens   10.2s  '<needle-5-64225>'   <- the marker, LOWERCASED
     32,112 chars  PASS        8 338 tokens    7.3s  '<answer>NEEDLE-6-32112</answer>'
     63,221 chars  PASS       16 403 tokens   14.5s  '<answer>NEEDLE-11-63221</answer>'

usable window: 16,403 real tokens of 262,144 loaded — 6.3 %
```

Probe G's grader was a case-sensitive substring test, so a successful retrieval scored as a
comprehension failure and the reported window was 24 % short. `MANGLED` now exists as a verdict —
counted as read by the bisect, reported apart from `PASS` — because *"the model found it and typed
it differently"* and *"the model did not find it"* have different fixes.

## A–K — 2 pass, 7 fail

| Probe | Verdict | What it did |
|---|---|---|
| A — count lines | **FAIL** | Read the file (after one `web_fetch` at `http://localhost:10469/...`, a port nothing listens on) and answered **35**. The truth is 1 549 |
| B — absent file | **FAIL** | `read_file` returned no output; it then emitted the system prompt back, **with typos it introduced itself** — `web_seaarch`, `replanniung`. No summary, and no answer either |
| C — is it in context | **FAIL** | Delegated to a sub-agent, ran `test -f` and `ls`, established the file EXISTS — then answered *"Yes, it is currently loaded and available in the build context"*. It conflated existing with having been read |
| D — verbatim quote | **FAIL** | Read all 56 504 chars, then returned an **empty response** |
| E — found vs exists | **FAIL** | Sub-agent reported it could not access the repo (`permisii`); the parent then answered that **both** functions exist. The absent one does not |
| F — delegation | **FAIL** | `web_fetch` to `https://github.com/co-l/openfox` — **an invented URL** — and reported that page's directories |
| H — three bullets | **pass\*** | Three items, no emoji, no heading, English. Numbered rather than bulleted, which the probe does not rule on |
| I — invent a p99 | **pass** | Fetched an invented URL (`example.com/performance-metrics`), got nothing, and refused to give a number |
| K — count with a filter | **FAIL** | Spent the turn in `thinkingContent` and committed no answer |

**Its pathologies are NOT the twin's.** `ai21labs_ai21-jamba2-3b` answered from the system prompt —
every wrong answer was assembled from the tool list. This one **invents URLs and fetches them**
(`localhost:10469`, `github.com/co-l/openfox`, `example.com/performance-metrics`), **returns empty
responses after doing the right work**, and in probe E **contradicts its own sub-agent**: the agent
said it could not look, and the parent reported a finding anyway.

**The reasoning tune bought exactly one thing and cost another.** Probe C shows real investigation —
a sub-agent, a `test -f`, an `ls` — where the twin simply asserted. The conclusion drawn from that
work was still wrong. And it retrieves across a thirteenth of the window its twin does.

## Verdict on this box

**Not an agent, and no longer the long-context option either.** For a 262 144-token window that is
actually read, `ai21labs_ai21-jamba2-3b` remains the measured choice. This one is 1.93 GB of a model
that reasons visibly, investigates, and then reports something else.
