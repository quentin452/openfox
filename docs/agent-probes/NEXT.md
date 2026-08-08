# What to run next

**This is the queue for local-model testing.** It is the only one — anything else claiming to say
what comes next here is a second copy, and two of those diverge. Delete a line when it is done and
fold what it found into `results/<model>.md`.

## Where it stands

Measured: **probe G only**, on three models. `results/` holds a file each, with the machine named.

Not measured: **probes A–F and H–K, on any model.** Those are the ones that measure honesty rather
than capacity — and honesty is what the kit exists for. Probe G was run first because a window is a
prerequisite, not because it is the interesting question.

## The queue, in order

1. **Full probe set A–K on `zai-org/glm-4.6v-flash`.** The only model whose window (122 333) and
   latency are both usable, so it is the baseline everything else is compared to. Expect probes B, C
   and E to be the ones it fails; they are the class that produced the whole kit.

2. **The A/B that says whether the rules do anything.** Re-run **B, C and E** on
   `qwen3.5-9b-deepseek-v4-flash`, once with OpenFox's global instructions in place and once with
   them cleared:

   ```bash
   cd ~/Documents/GitHub/Claude-Conf-Backup
   python3 scripts/openfox-config/apply_global_instructions.py --clear   # then run B, C, E
   python3 scripts/openfox-config/apply_global_instructions.py --apply   # then run them again
   ```

   The unstructured session of 2026-08-08 failed all three without them (it claimed to have read a
   file it had never opened, and cited it as a source). **That is the before.** If the after is
   identical, the instructions are decoration and belong in the skill instead — which is a finding
   worth more than a green run.

3. **Probe K with RTK toggled.** OpenFox's *Enable RTK auto-rewrite* filters command output and
   truncates multi-match listings to about 25 lines, replacing the rest with a pointer. Ask for a
   count the true value of which is far above that (`<SYMBOL_COMMON>` in the key), with the toggle
   on and off. The gap between the two answers is what the filter costs in correctness, against the
   tokens it saves.

4. **`prism-ml/bonsai-27b`: throughput, not depth.** Its ladder stopped at a client timeout, not a
   limit — its loaded context is 126 720 and the run stopped at 64 000. But it took 317 s at 32 000
   where the 9 B takes 45 s, so the question that decides whether it is usable is tokens per second
   at a fixed context, not how deep it can go. Measure that first; only then decide whether more
   depth is worth the wall-clock.

5. **Re-measure a window whenever the machine changes.** A new LM Studio version, a driver update,
   another card, or a different `--gpu` ratio all move it. `lmstudio.sh status` prints declared and
   loaded side by side, and `results/` records the machine for exactly this reason.

## How to run one without producing a wrong number

```bash
./lmstudio.sh load <model> <ctx> max          # pin the model, the context and the offload
./ground-truth.sh /path/to/target/repo ./key  # regenerate the key AND the needles
```

Three ways a run has already produced a wrong number here, all of them recorded in `PROBES.md`:

- **Retyping the marker.** It is derived from the target repository's HEAD; a commit between
  generating the key and running the probe changes it, and a runner holding its own copy reports the
  model failing when the model was right. Read the marker out of the needle file.
- **Confusing a refusal, a failure and a timeout.** An HTTP 400 in a second is the server's context
  limit and the model never saw the text. A client timeout measures your own patience. Neither is
  the model getting it wrong.
- **Comparing configurations while claiming to compare models.** Where the KV cache lives is worth
  6× at the same depth, and full offload does not fit for every model on every card. Record the
  setting beside the latency.
