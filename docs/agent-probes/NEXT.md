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

6. **Probe L on every model already measured** — the new capability probe (`PROBES.md` §L). It is
   three arithmetic questions with exact answers: a yaw-rotated box's AABB, a triangle's unit normal
   and area, a silhouette width. **It exists because the point of this kit is a `.catz` shape genre
   that does not exist yet**, and a model that cannot normalise a cross product cannot author or
   review a parametric solid however honest it is. Cheap — no repository, no window, no tools
   needed — so it runs on `lfm2.5-2.6b` and `qwen3.5-9b-deepseek-v4-flash` in minutes and says
   whether the small end of the range is usable for geometry content at all. Record whether the
   answer was computed, tool-called, or asserted; the third is untrustworthy even when right.

7. **The long-context candidates, and what has to be checked before downloading any of them.**
   The shortlist below came from a chat answer, so **treat every line as a claim until the repo says
   it**: the trap is a plausible spec for a model that does not exist under that name.

   | Candidate | Status of the claim | What decides it here |
   |---|---|---|
   | `ai21labs/AI21-Jamba2-3B` | **Verified**: 256k context, tool use documented (`--tool-call-parser hermes` in its own quickstart), Apache 2.0. `config.json` read: **28 layers, attention period 14 offset 7 — so 2 attention layers**, 1 KV head, head_dim 128 | **KV cache at 262 144 tokens is ~0.26 GiB.** Weights ~1.9 GB at Q4. It would sit in about 2.5 GB of a 12 GB card *with its whole declared window*, which no dense model here can do. **The open question is a GGUF: llama.cpp carries a `jamba` arch and AI21 publish GGUF for other family members, but a Jamba2-3B GGUF was not confirmed.** Check that first — `lms get` on a safetensors-only repo fails |
   | `Qwen/Qwen3-30B-A3B-Instruct-2507` | **Verified**: 262 144 native, 30.5 B total / 3.3 B active, 128 experts 8 active, 48 layers, 4 KV heads, strong tool calling | **Does not fit this box at its window.** MoE saves compute, not memory: all 30.5 B of weights must be resident (~18 GB at Q4) and the KV cache is a dense 48-layer one, ~96 KiB/token — **24 GiB at 256k, 12 GiB at 128k**. Against 12 GB of VRAM and 31 GB of RAM, 18 + 12 is the whole machine. Worth measuring only at a short window, and then it is competing with the 9 B that already scores 10 of 11 |
   | "Ministral 3 3B Instruct, 256k" | **Unverified — and the number is suspect.** Mistral's published Ministral 3B is a 128k model | Find the actual repo before planning a run. If the 256k variant does not exist, this line is a hallucinated spec and should be deleted rather than carried |
   | `amd/Instella-3B-Long-Instruct` | **Unverified** | Same: confirm the repo, the context, and whether it tool-calls at all before it costs a download |

   **The order that wastes the least: confirm the GGUF, compute the cache from `config.json`, then
   download.** Jamba2-3B is the only candidate whose architecture makes 256k cheap on this card, so
   it is the one worth the check.

8. **Or fine-tune `lfm2.5-2.6b` instead — and note what that would and would not fix.** It already
   scores 8/1/2 and loads its full 128 000. Its measured gap is **comprehension**, not window: it
   uses 66.2 % of what it loads, where the 9 B uses 99.7 %. Fine-tuning changes behaviour — refusal
   phrasing, tool discipline, format adherence — and **a fine-tune does not extend the window it can
   actually reason across**; that is architecture and training length. So it is the right lever for
   the probes it fails on behaviour, and the wrong one for the 84 707 ceiling. Probe L (item 6) says
   whether the arithmetic is there to build on before any of this is worth doing.

9. **Re-measure a window whenever the machine changes.** A new LM Studio version, a driver update,
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
