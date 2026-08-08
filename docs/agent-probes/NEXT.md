# What to run next

**This is the queue for local-model testing.** It is the only one — anything else claiming to say
what comes next here is a second copy, and two of those diverge. Delete a line when it is done and
fold what it found into `results/<model>.md`.

## Where it stands

**`lfm2.5-2.6b` is measured end to end** — window 84 707 of 128 000 loaded (66.2 %), and A–K at
**8 pass / 1 fail / 2 inconclusive**. `results/lfm2.5-2.6b.md` has the table and the transcript
notes. Probe G is now `find-window.py` (bisects from the loaded ceiling instead of climbing a
ladder) and the rest run from a terminal through `run-probe.py`.

**Probe K failed and caught RTK doing it** — the model ran the right `grep … | wc -l` four times and
answered 205 where the truth is 17 587, with a subdirectory reporting more matches than the tree
containing it. RTK truncates output to about 25 lines, so `wc -l` counted the filter. That is the
failure this kit was written for, caught in the act for the first time.

**`zai-org/glm-4.6v-flash` is out of the running:** it cannot complete a tool-calling turn — it
repeats one call until `max_tokens` and nothing dispatches. Measured from both ends in
`results/zai-org-glm-4.6v-flash.md`; qwen does the same request cleanly four times out of four.

**`qwen3.5-9b-deepseek-v4-flash` is measured end to end, 2026-08-08** — **10 of 11**, with
`global_instructions` in place. Window 127 563 of 128 000 loaded (**99.7 %**), and every refusal
above it is the server's in under three seconds: this model hits the context limit, never a
comprehension limit. Only probe K fails, and **not in the way K tests** — it counted rather than
reading a truncated list, and answered 17 629 against a key of 17 587 by globbing a different scope.
`results/qwen3.5-9b-deepseek-v4-flash.md` has the table.

**The queue's own prediction was refuted, which is the finding.** This file said to expect B, C and E
to fail, because they are the class that produced the kit. All three passed. The evidence they were
named on came from an _unstructured_ session against the same model, so what changed is the harness,
the mode, or the instructions — and one arm cannot say which. Item 3 below is now the measurement
that matters most.

Not measured: **A–K on `prism-ml/bonsai-27b` or `zai-org/glm-4.6v-flash`** (the latter cannot
tool-call at all, see its result file).

## The queue, in order

1. **Re-run probe C on `lfm2.5-2.6b`.** It is the only one still unscored, and the reason was the
   runner rather than the model: it returned as soon as `isRunning` went false, which is before the
   final text commits, so every answer landed against the following question. Fixed — but the fix is
   unproven, and C is the probe the whole kit exists for.

2. **The two questions the rules exist to answer, and they are one run.** Does the model call
   `load_skill("regles-agent")` before working on a repository, unprompted — the instruction is
   deliberately unconditional — and once loaded, does it quote the skill or invent it? The second has
   a computed key: ask for the `git add -A` rule, which is in `SKILL.md` and **not** in the system
   prompt, and for a branch-naming rule, which is in neither. Inventing the second is the failure
   that matters.

3. **The A/B that says whether the rules do anything.** Re-run **B, C and E** on
   `qwen3.5-9b-deepseek-v4-flash`, once with OpenFox's global instructions in place and once cleared:

   ```bash
   cd ~/Documents/GitHub/Claude-Conf-Backup
   python3 scripts/openfox-config/apply_global_instructions.py --clear   # then run B, C, E
   python3 scripts/openfox-config/apply_global_instructions.py --apply   # then run them again
   ```

   **The _after_ arm is already measured**: the A–K run of 2026-08-08 had `global_instructions`
   applied and B, C and E all passed. So what is missing is the **cleared** arm, run the same way —
   through `run-probe.py`, in planner mode, one fresh session per probe. That matters, because the
   only _before_ on record is an unstructured browser session, and comparing it to a runner session
   compares two harnesses as much as two instruction sets. If the cleared arm passes too, the
   instructions are decoration and belong in the skill instead — a finding worth more than a green
   run.

4. **Probe K with RTK toggled, now that one half is measured.** With RTK on, `lfm2.5-2.6b` answered
   205 against a true 17 587. What is missing is the same probe with the toggle **off**: the gap
   between the two answers is what the filter costs in correctness, against the tokens it saves. A
   model that gives the same number both times is one that counted instead of reading.

5. **`prism-ml/bonsai-27b`: throughput, not depth.** Its ladder stopped at a client timeout, not a
   limit — loaded context 126 720, run stopped at 64 000. But it took 317 s at 32 000 where the 9 B
   takes 45 s, so what decides whether it is usable is tokens per second at a fixed context. Measure
   that first. **It also JIT-loads at 8.6 GiB** when anything addresses it, so unload it afterwards.

6. **Re-measure a window whenever the machine changes.** A new LM Studio version, a driver update,
   another card, or a different `--gpu` ratio all move it. `lmstudio.sh status` prints declared and
   loaded side by side, `find-window.py` re-runs the whole of probe G in one command, and `results/`
   records the machine for exactly this reason.

## How to run one without producing a wrong number

```bash
./lmstudio.sh load <model> <ctx> max          # pin the model, the context and the offload
./find-window.py --model <model>              # probe G, from the loaded ceiling down
./ground-truth.sh /path/to/target/repo ./key  # regenerate the key AND the needles
./run-probe.py --repo <target> --model <model> --mode planner "<probe>"
```

Five ways a run has already produced a wrong number here, all of them recorded in `PROBES.md`:

- **Retyping the marker.** It is derived from the target repository's HEAD; a commit between
  generating the key and running the probe changes it, and a runner holding its own copy reports the
  model failing when the model was right. Read the marker out of the needle file.
- **Confusing a refusal, a failure and a timeout.** An HTTP 400 in a second is the server's context
  limit and the model never saw the text. A client timeout measures your own patience. Neither is
  the model getting it wrong.
- **Comparing configurations while claiming to compare models.** Where the KV cache lives is worth
  6× at the same depth, and full offload does not fit for every model on every card. Record the
  setting beside the latency.
- **Grading the field the model did not answer in.** A thinking model puts its answer in
  `reasoning_content` and can leave `content` empty; a runner that reads only `content` scores it
  wrong at every depth and reports a window of zero for a model that was right. `find-window.py`
  reads both, and treats its own output cap as its own verdict rather than as the model's failure —
  that is what `TRUNCATED` is for.
- **Reading the transcript before the answer is in it.** A session's `isRunning` flips before the
  final assistant text is committed, so a runner that returns there captures the turn without its
  answer — and the answer surfaces at the top of the NEXT probe's output. An eleven-probe session was
  graded one question out of step before anybody noticed, because a misaligned transcript reads
  perfectly well.
