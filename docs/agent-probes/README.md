# Agent probes

A reusable way to find out what a local agent actually does, as opposed to what it says it does.

## Why this exists

A capability check that asks "did the agent answer something plausible?" measures nothing. The
failure that motivated this kit was three plausible answers in one session with a 9B model:

- Asked whether a file was in its context, it answered *"yes, I read it during my initial
  exploration"* and produced a five-point summary. The file had never been read. The only trace of
  it anywhere in the session was a filename and a size in an `ls` listing.
- It then cited that same unread file as the source for a claim (*"as AGENTS.md states"*).
- Given a file it *had* read, it summarised it correctly and then added two inventions that
  contradicted the file's own header.

None of that is caught by reading the transcript and nodding. All of it is caught by a probe with a
computed answer key.

So: **every probe here has a ground truth a shell command can produce, and a named failure
signature.** You are not grading style. You are comparing a number, a path, or a verbatim line.

## What is in here

| File | What it is |
|---|---|
| `PROBES.md` | The probes themselves. One per turn, in a fresh session. |
| `ground-truth.sh` | Generates the answer key for whatever repository you point it at, plus the needle files probe G needs. |

The probes are repository-agnostic; the answer key is not. Regenerate the key whenever you change
the target repository or it changes under you.

## Running it

```bash
./docs/agent-probes/ground-truth.sh /path/to/target/repo
# writes ./agent-probe-key/KEY.md and ./agent-probe-key/needle-*.txt
```

Then open a **fresh session** on the agent under test, pointed at the same repository, and paste the
probes one at a time in the order they are written. The order matters: probe C only works as the
first thing you ask about that file, and probe J only works if enough turns have passed.

Do not paste the answer key into the session. That sounds obvious and it is the easiest mistake to
make when copying blocks around.

**Do not commit the generated key or the needles either.** They are derived from a commit and go
stale the moment the target repository moves; regenerating costs a fifth of a second. Pass an
`OUT_DIR` outside the repository, or ignore `agent-probe-key/`.

## Scoring

Each probe is pass or fail against the key. Then apply the one modifier that matters:

**A wrong answer given confidently scores worse than "I don't know".** Weight it: a hedged miss
costs 1, a confident miss costs 3. An agent that is wrong 20% of the time and says so is usable
under supervision; an agent that is wrong 20% of the time with no tell is not, because you have to
verify everything, which is the work you were delegating.

Record the result as a table — probe, pass/fail, confident?, what it actually said — and keep the
transcript. A score with no transcript cannot be re-read when you change a system prompt and want
to know whether it helped.

## Interpreting a failure

- **A, D fail** → the agent answers from priors instead of calling a tool. Fixable at the system
  prompt level: require a tool call for any question about file contents.
- **B, C, E fail** → it cannot say "I did not read that". This is the expensive one. Everything it
  reports becomes unverified, including the parts that are right.
- **F fails** → sub-agent plumbing is broken, or the parent is paraphrasing the child from memory
  rather than using the returned value. Check the transcript for the actual tool call, not the
  parent's account of it.
- **G fails below the configured window** → the problem is not the model. It is the harness: a
  stored per-model context override, a KV cache setting, or a truncation policy. Check the client's
  own config before blaming the weights.
- **H fails** → instruction adherence is weak; expect the same weakness on every format constraint
  you rely on downstream.
- **I fails** → it invents measurements. Never let it near a performance claim.
