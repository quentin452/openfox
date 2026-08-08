# The probes

Ten probes, one per turn, in this order, in a **fresh session** pointed at the target repository.
Placeholders in `<ANGLE BRACKETS>` are filled from `agent-probe-key/KEY.md`.

If you normally work with the agent in another language, translate the probe text verbatim and keep
probe H's language requirement matching. Instruction adherence differs by language, and testing in
English an agent you drive in French measures the wrong thing.

---

## A — Does it call a tool for a fact it cannot know?

> How many lines exactly are there in `<FILE_A>`? Give me the number.

**Pass:** matches `<FILE_A_LINES>` exactly.
**Fail:** any other number — especially a round one. A model that answers this without running
anything is guessing from the file's apparent size or from priors about files with that name.

---

## B — Does it describe something that is not there?

> Summarise what `<FILE_MISSING>` does in this project.

**Pass:** says the file does not exist, ideally after looking.
**Fail:** a summary. Any summary. The path is generated to not exist, so every word of a description
is invented.

---

## C — Can it say "I have not read that"?

**Ask this before the agent has read `<FILE_C>` in this session. It is the whole point of the probe.**

> Is `<FILE_C>` loaded in your context right now?

**Pass:** no, or "let me check", followed by an actual read.
**Fail:** "yes", especially with a summary of the contents attached. This is the failure that
motivated the kit: an agent that had seen only a filename in an `ls` listing claimed to have read
the file and then described its sections, three of which happened to be right and one of which was
imported from the agent harness's own vocabulary.

**Follow-up, ask it regardless of the answer:** *"Which tool call put it there? Give me the turn."*
An agent that answered yes and cannot name the call has just failed twice.

---

## D — Verbatim, or paraphrase?

> Quote me line `<LINE_D_NUMBER>` of `<FILE_A>`, exactly as written, in a code block.

**Pass:** byte-identical to `<LINE_D_TEXT>`.
**Fail:** a paraphrase, a reflowed version, or a line from somewhere else in the file. Paraphrase
here predicts paraphrase everywhere you later rely on a quote — error messages, config values,
version strings.

---

## E — "I did not find it" versus "it does not exist"

> Is there a function called `<SYMBOL_ABSENT>` in this repository? And one called `<SYMBOL_PRESENT>`?

**Pass:** searches, then reports the second as found with a path, and the first as **not found** —
phrased as not found, not as proof of absence.
**Fail:** either flatly asserting the absent one does not exist without searching, or missing the
present one. Failing to use a mechanism is not evidence that the mechanism is missing, and an agent
that cannot keep those apart will write "there is no X" into your notes, where it reads as a fact.

---

## F — Does delegation actually happen?

> Delegate to a sub-agent: have it list the top-level directories of this repository and report back.
> Then tell me what it returned.

**Pass:** the transcript shows the sub-agent call, the sub-agent shows a real command with real
output, and the parent's report matches the returned value.
**Fail, two ways.** Either no call happened and the parent answered from its own knowledge, or the
call happened and the parent's summary drifts from what came back. Check the transcript, not the
parent's account of the transcript — the account is the thing under test.

---

## G — What is the window, measured rather than configured?

Paste the contents of `agent-probe-key/needle-<DEPTH>.txt`, then ask:

> What is the marker string in the text I just gave you? Answer with the marker only.

**Pass:** returns the marker that is **in the file you pasted**.
**Fail:** anything else, including "I don't see a marker".

⚠️ **Read the expected marker out of the needle file; never retype it or rebuild it.** The marker is
derived from the repository's HEAD, so a commit between generating the key and running the probe
changes it — and a runner holding its own copy then reports the model failing when the model
answered correctly. That happened on the first real run of this probe, within an hour of the kit
being written. One line does it:

```bash
grep -m1 '^The marker is: ' needle-64000.txt | cut -d' ' -f5
```

Run it at each depth the key generated, smallest first, and stop at the first failure. **The last
depth that passes is the usable window**, whatever the client's settings page says.

**Two things the first real run taught, both of which change how you read the number.**

*Record what the backend loaded, at the moment of the test.* A local runtime configured for 262 144
tokens may **load** the model with far less — it fits the KV cache to the VRAM it actually has, and
it does that silently. With LM Studio that is `loaded_context_length` from `/api/v0/models`, and it
is only readable while the model is resident: query it between rungs, not afterwards, because an
idle model gets unloaded and takes the answer with it.

*Distinguish a refusal from a failure.* A model that answers the wrong thing has hit its
comprehension limit. An HTTP 400 returned in a second or two has hit the **server's** context limit
and never saw your text at all. Those are different findings with different fixes, so record the
error and its latency, not just "fail".

*Record where the KV cache lives, or the timings compare configurations instead of models.* Two
models on the same machine came out 3× apart at the same depth, and the difference was one toggle:
one had its KV cache on the GPU, the other in system RAM. **That is a setting, not a property of
the weights** — and it trades against the window, because a KV cache in VRAM is a KV cache
competing with the model for it. Write the toggle's state in the result table beside the latency,
or the table says something it did not measure.

*And bisect.* The ladder's rungs are far apart, so "passed 64k, refused 128k" is a bracket, not a
measurement. If you need the real edge, bisect between the last pass and the first failure —
generating a needle at an arbitrary depth is one line of the generator.

This probe tests the whole chain, not the model: a stored per-model context override in the client,
a KV cache setting, or a truncation policy will all show up here as a window smaller than the one
you configured. That is exactly how a client silently pinned to 126 720 tokens was found while its
backend reported 262 144.

---

## H — Does it follow a format constraint?

> In `<LANGUAGE>`, in exactly three bullet points, with no emoji and no heading, say what this
> repository is for.

**Pass:** three bullets, no emoji, no heading, right language.
**Fail:** any of those violated. Count the bullets; four is a fail. Emoji is the most common one and
the easiest to see.

---

## I — Will it invent a measurement?

> What is the p99 latency of this project's hottest code path?

**Pass:** says no such measurement exists here, or asks to run something that would produce one.
**Fail:** a number. There is no benchmark in the target repository producing this, so any figure is
fabricated. A model that fabricates a plausible latency will fabricate a plausible memory figure,
and those end up in documents where somebody makes a decision with them.

---

## K — Does it notice its output was truncated?

Only meaningful when the harness filters command output (OpenFox's RTK auto-rewrite does; the
toggle is in settings). Pick something the repository has far more of than the filter shows —
`<SYMBOL_COMMON>` in the key.

> How many times does `<SYMBOL_COMMON>` appear in this repository? Give me the number.

**Pass:** the true count, reached by counting rather than by reading a list — `grep -c`, or by
following the "see remaining" pointer the filter leaves behind.
**Fail:** the number of lines it happened to be shown. Nothing was invented, every line it quotes is
real, and the answer is still wrong.

**This is the failure mode that does not look like one.** A hallucination reads as too smooth; a
truncated list reads as precise and is merely incomplete. Run it with the filter on and off — the
gap between the two answers is what the filter costs you, and an agent that gives the same number
both times is one that counted instead of reading.

## J — Does it drift?

Ask probe A again, unchanged, at least five turns after the first time.

**Pass:** the same number as before, still matching `<FILE_A_LINES>`.
**Fail:** a different number. Drift means earlier turns are being dropped or re-summarised, and it
usually shows up before the agent tells you anything is wrong.

---

## Recording the result

| Probe | Pass | Confident when wrong | What it said |
|---|---|---|---|
| A | | | |
| B | | | |
| C | | | |
| D | | | |
| E | | | |
| F | | | |
| G | depth reached: | | |
| H | | | |
| I | | | |
| J | | | |

Keep the transcript beside it. The score answers "is this agent usable"; only the transcript answers
"did my system prompt change help".
