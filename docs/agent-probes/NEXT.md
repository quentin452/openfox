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

**`ai21labs/AI21-Jamba2-3B` is measured end to end, 2026-08-08, and it splits the two questions
this kit exists to keep apart.** It is the first model here whose loaded context equals its declared
one — **262 144 loaded, 3 342 MiB of VRAM**, predicted from `config.json` before the download (two
attention layers out of 28, one KV head → about 0.26 GiB of cache at 256k) — and it retrieves a
marker at **262 055 tokens, 100 % of what it loads**. It also scores **2 of 9 on A–K**: it cannot
run a shell loop, and every wrong answer it gave was assembled from the system prompt's own tool
list. **A window that loads is not a window a model reasons across, and neither one predicts whether
it can act.** `results/ai21labs-jamba2-3b.md` has both tables.

**`ai21labs/AI21-Jamba-Reasoning-3B` is measured, 2026-08-08, and it is the cleanest comparison the
kit has made.** Its `config.json` matches `ai21labs_ai21-jamba2-3b`'s on every field that decides
cost — 28 layers, 2 attention, 1 KV head, 262 144 — and both load their full declared window. The
twin reads **100 %** of it. This one reads **6.3 %**, and where the twin's failures were the server
refusing, this one's are the model answering wrong. **Post-training, not architecture, decided the
usable window.** A–K: 2 pass, 7 fail, with pathologies of its own — invented URLs that it then
fetches, empty responses after doing the reading, and a parent that contradicted its own sub-agent.

**A community fine-tune was tested and it separates the two purchases, 2026-08-08.**
`cybertruck32489/Jamba-Reasoning-3B-Agent-v1` carries an empty auto-generated card, so running it
was the only way to learn what it holds: its usable window is **85 452 tokens against its base's
16 403 — 5.2×** — and it scores **1 of 9** on A–K where the base scored 2. Someone trained long
context and wrote "Agent" on the box. It also **fabricated a `<tool_response>` block** in its own
output, at the exact shape the harness produces, with an invented exit code — see item 3.
`results/jamba-reasoning-3b-agent-v1.md`.

## The queue, in order

1. **Re-run probe G on `ai21-jamba-reasoning-3b` with the fixed grader.** Measured 2026-08-08 at
   **6.3 % of what it loads** — 16 403 tokens of 262 144 — but the run predates `MANGLED`: at
   16 675 tokens it returned the marker LOWERCASED and the case-sensitive grader scored it WRONG.
   The honest edge is between ~16.7 k and ~33.7 k, and one re-run closes it. **The finding stands
   either way and it is the sharpest one this kit has produced**: this model's `config.json` is
   identical to `ai21labs_ai21-jamba2-3b`'s on every field, and the twin reads 100 % of the same
   loaded window while failing only at the server's refusal. Same shape, different post-training,
   a fortieth of the usable context. A–K: **2 pass, 7 fail** — it invents URLs and fetches them,
   returns empty responses after reading the file, and contradicts its own sub-agent.
   `results/ai21-jamba-reasoning-3b.md` has both tables.

2. **Re-run probe G on `lfm2.5-2.6b` too**, for the same reason: its recorded WRONG depths predate
   `MANGLED`, and a marker returned in the wrong case would have scored as a comprehension failure
   there as well. Its edge of 84 707 can only move up.

3. **Check whether OpenFox can be fed a forged tool result.** `Jamba-Reasoning-3B-Agent-v1` wrote
   a complete `<tool_response>` block into its own assistant text — right shape, invented exit code
   — for a command it never ran. **If the server parses tool results out of the assistant stream
   rather than from its own dispatcher, a model can forge evidence**, and every probe that grades a
   transcript is then grading something the model wrote. This is a code question, not a model one,
   and it outranks the rest of this queue because it decides whether the transcripts this kit reads
   can be trusted at all.

4. **Add a per-turn watchdog to the runner.** Probe C hung for twelve minutes with
   `isRunning: true` while LM Studio was IDLE and the assistant message was empty — a model that
   leaks control tokens can stall a turn that has finished. `run-probe.py` waits out its whole
   timeout for that; the kit should report `STALLED` and move on.

5. **`ai21labs_ai21-jamba2-3b` is MEASURED and it is not an agent. Nothing left to run on it
   except L.** Probe G: **262 055 usable tokens of 262 144, 100 %**, every failure above it the
   server's refusal and never a wrong answer. A–K: **2 pass, 7 fail** — it invented a tool name
   rather than report one missing, ran the same failing command 23 times, said a file it had never
   read was "loaded in context", and answered `0` for a count of 17 587 by misreading an error.
   **Every wrong answer was built out of the system prompt's own tool list**, which is the tell.
   `results/ai21labs-jamba2-3b.md` has the table and the receipts.
   **What that pair proves is worth more than either number:** retrieval at 262k predicts NOTHING
   about agent competence. The two measurements are orthogonal, and this is the first model here to
   separate them cleanly — so a window measurement alone must never again be read as a verdict on a
   model. L is still worth running on it (cheap, no repo, no tools) to see whether the arithmetic
   holds up where the agency does not.

6. **Re-run probe C on `lfm2.5-2.6b`.** It is the only one still unscored, and the reason was the
   runner rather than the model: it returned as soon as `isRunning` went false, which is before the
   final text commits, so every answer landed against the following question. Fixed — but the fix is
   unproven, and C is the probe the whole kit exists for.

7. **The two questions the rules exist to answer, and they are one run.** Does the model call
   `load_skill("regles-agent")` before working on a repository, unprompted — the instruction is
   deliberately unconditional — and once loaded, does it quote the skill or invent it? The second has
   a computed key: ask for the `git add -A` rule, which is in `SKILL.md` and **not** in the system
   prompt, and for a branch-naming rule, which is in neither. Inventing the second is the failure
   that matters.

8. **The A/B that says whether the rules do anything.** Re-run **B, C and E** on
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

9. **Probe K with RTK toggled, now that one half is measured.** With RTK on, `lfm2.5-2.6b` answered
   205 against a true 17 587. What is missing is the same probe with the toggle **off**: the gap
   between the two answers is what the filter costs in correctness, against the tokens it saves. A
   model that gives the same number both times is one that counted instead of reading.

10. **`prism-ml/bonsai-27b`: throughput, not depth.** Its ladder stopped at a client timeout, not a
   limit — loaded context 126 720, run stopped at 64 000. But it took 317 s at 32 000 where the 9 B
   takes 45 s, so what decides whether it is usable is tokens per second at a fixed context. Measure
   that first. **It also JIT-loads at 8.6 GiB** when anything addresses it, so unload it afterwards.

11. **Probe L on every model already measured** — the new capability probe (`PROBES.md` §L). It is
   three arithmetic questions with exact answers: a yaw-rotated box's AABB, a triangle's unit normal
   and area, a silhouette width. **It exists because the point of this kit is a `.catz` shape genre
   that does not exist yet**, and a model that cannot normalise a cross product cannot author or
   review a parametric solid however honest it is. Cheap — no repository, no window, no tools
   needed — so it runs on `lfm2.5-2.6b` and `qwen3.5-9b-deepseek-v4-flash` in minutes and says
   whether the small end of the range is usable for geometry content at all. Record whether the
   answer was computed, tool-called, or asserted; the third is untrustworthy even when right.

12. **The long-context candidates, and what has to be checked before downloading any of them.**
   The shortlist below came from a chat answer, so **treat every line as a claim until the repo says
   it**: the trap is a plausible spec for a model that does not exist under that name.

   | Candidate                          | Status of the claim                                                                                                                                                  | What decides it here                                                                                                                                                                                                                                                                                                                                                                                         |
   | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
   | `ai21labs/AI21-Jamba2-3B`          | **DOWNLOADED AND LOADED** — the GGUF question is answered: `bartowski/ai21labs_AI21-Jamba2-3B-GGUF`, Q4_K_M, 1.86 GB. See item 1 and `results/ai21labs-jamba2-3b.md` | **Loaded 262 144 = declared, 3 342 MiB of VRAM**, matching the 0.26 GiB cache predicted from `config.json`. Only its honesty and its tool use are still unmeasured                                                                                                                                                                                                                                           |
   | `Qwen/Qwen3-30B-A3B-Instruct-2507` | **Verified**: 262 144 native, 30.5 B total / 3.3 B active, 128 experts 8 active, 48 layers, 4 KV heads, strong tool calling                                          | **Does not fit this box at its window.** MoE saves compute, not memory: all 30.5 B of weights must be resident (~18 GB at Q4) and the KV cache is a dense 48-layer one, ~96 KiB/token — **24 GiB at 256k, 12 GiB at 128k**. Against 12 GB of VRAM and 31 GB of RAM, 18 + 12 is the whole machine. Worth measuring only at a short window, and then it is competing with the 9 B that already scores 10 of 11 |
   | "Ministral 3 3B Instruct, 256k"    | **Unverified — and the number is suspect.** Mistral's published Ministral 3B is a 128k model                                                                         | Find the actual repo before planning a run. If the 256k variant does not exist, this line is a hallucinated spec and should be deleted rather than carried                                                                                                                                                                                                                                                   |
   | `amd/Instella-3B-Long-Instruct`    | **Unverified**                                                                                                                                                       | Same: confirm the repo, the context, and whether it tool-calls at all before it costs a download                                                                                                                                                                                                                                                                                                             |

   **The order that wastes the least: confirm the GGUF, compute the cache from `config.json`, then
   download.** Jamba2-3B is the only candidate whose architecture makes 256k cheap on this card, so
   it is the one worth the check.

13. **Or fine-tune `lfm2.5-2.6b` instead — and note what that would and would not fix.** It already
   scores 8/1/2 and loads its full 128 000. Its measured gap is **comprehension**, not window: it
   uses 66.2 % of what it loads, where the 9 B uses 99.7 %. Fine-tuning changes behaviour — refusal
   phrasing, tool discipline, format adherence — and **a fine-tune does not extend the window it can
   actually reason across**; that is architecture and training length. So it is the right lever for
   the probes it fails on behaviour, and the wrong one for the 84 707 ceiling. Probe L (item 6) says
   whether the arithmetic is there to build on before any of this is worth doing.

14. **Re-measure a window whenever the machine changes.** A new LM Studio version, a driver update,
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
