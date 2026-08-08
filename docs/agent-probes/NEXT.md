# What to run next

**This is the queue for local-model testing.** It is the only one — anything else claiming to say
what comes next here is a second copy, and two of those diverge. Delete a line when it is done and
fold what it found into `results/<model>.md`.

## Where it stands

**`lfm2.5-2.6b` is measured end to end** — window 84 707 of 128 000 loaded (66.2 %), and A–K at
**8 pass / 1 fail / 2 inconclusive**. `results/lfm2.5-2.6b.md` has the table and the transcript
notes. Probe G is now `find-window.py` (bisects from the loaded ceiling instead of climbing a
ladder) and the rest run from a terminal through `run-probe.py`.

**Re-run with the `MANGLED` grader, 2026-08-08: the same nine depths, the same nine verdicts, the
same 84 707 — and this file's prediction that it "can only move up" was wrong.** The correction that
moved `ai21-jamba-reasoning-3b` by 24 % applies to a model that returns the marker in the wrong case,
and this one never did: zero `MANGLED` in the whole run. **What the re-run bought instead is the
first evidence the bisect is deterministic** — two runs days apart, wildly different timings, identical
verdicts. A kit whose stated worry is producing a wrong number now has one measurement it has seen twice.

**Probe K failed and caught RTK doing it** — the model ran the right `grep … | wc -l` four times and
answered 205 where the truth is 17 587, with a subdirectory reporting more matches than the tree
containing it. RTK truncates output to about 25 lines, so `wc -l` counted the filter. That is the
failure this kit was written for, caught in the act for the first time.

### The selection rule: a SMALLER context that is GOOD beats a bigger one that hallucinates

**Ruling, 2026-08-08.** 128 000 tokens a model stays correct across is worth more than 262 144 it
fills with invention. **A window is not a score, and this file must stop reading it as one** — the
headline number for a model is what it can be trusted to do across its window, never the window.

**The kit had already proved this and had not drawn the conclusion.** `ai21labs_ai21-jamba2-3b`
retrieves a marker at **262 055 tokens, 100 %** — the best window measured here — and scores **2 of 9
on A–K**, inventing a tool name rather than reporting one missing, running the same failing command
23 times, and calling a file it had never read "loaded in context". Probe L then found the same shape
in arithmetic: it lost its own inputs mid-derivation and printed `1.414176` for a value it had just
written as `≈1.4142`. **Retrieval at 262k predicts nothing about staying correct at 262k**, and this
rule is what that separation is FOR.

**What it selects, on today's measurements:** `qwen3.5-9b-deepseek-v4-flash` — 127 563 of 128 000
loaded (**99.7 %**), **10 of 11** on A–K, every refusal above its ceiling the server's in under three
seconds. It is already installed and already measured. jamba2-3b keeps the long-context crown and
loses the selection.

**And the two rulings meet on one probe.** Qwen's single failure is **K**, and K is the
truncation-recovery capability the ruling below names. So the most valuable single run in this queue
is K re-run on qwen under the three-outcome grading — its recorded failure was *"not in the way K
tests"* (it counted rather than reading a truncated list, and globbed a different scope to answer
17 629 against a key of 17 587), so what the best model here actually does with a truncation marker
**has never been measured**.

### The ruling on RTK: the target is the MODEL, not the filter

**Ruling, 2026-08-08.** Fixing RTK is the smaller move. What this kit should be measuring — and what
a fine-tune should be buying — is a model that **notices its output was truncated and corrects its
own trajectory**, because truncation is not an RTK quirk: it is what every pager, every log tail and
every tool with a cap does to an agent.

**The prerequisite was checked before the ruling was written, because a model cannot be trained to
detect something invisible.** RTK marks its own truncation, inline, with the recovery path attached:

```
  +9 more in crates/catz-core/src/solid/project.rs [see remaining: tail -n +26 ~/.local/share/rtk/tee/…log]
```

Signal present, remedy printed. So this is not detection of an invisible thing — it is obedience to
a marker that is already on the screen.

**Which explains probe K exactly, and splits it into two behaviours rather than one.** The model ran
`grep … | wc -l`. The pipe consumes output that RTK has *already* filtered, markers included, so the
model never saw `+N more` — it saw `205`. The truncation was not ignored, it was destroyed upstream
of the model's eyes. So:

1. **Never compute an aggregate over filtered output** — `wc -l`, `head -1`, any count. The filter
   sits upstream of the arithmetic, so the number counts the filter. A true total needs `rtk proxy`.
2. **`+N more` or `see remaining:` on screen → follow the printed `tail`, or re-run through
   `rtk proxy`, before concluding anything about the content.**

**Seen a second time, 2026-08-08, in a CatzEngine session, by a model that then caught itself:**
`grep "^## D" docs/DECISIONS.md | tail -4` returned D022, D023, D024 — the *earliest* entries — when
it was asked for the last ones, because `tail` took the last four of RTK's 25-line window. The
`+41 more` marker was visible in the same output. `rtk proxy` gave the truth: 62 decisions, last
`D062`. Same shape as probe K's 205, one pipe further along.

**What this changes below:** the *probe K* item stops being "measure what the filter costs" and
becomes the **eval** of this capability; the *fine-tune `lfm2.5-2.6b`* item gains a named target, and
it is the right kind — behaviour, not window.

**Items are referred to by NAME here, never by number.** Deleting a done line renumbers everything
under it, and four cross-references in this file were already pointing at the wrong item before
anybody noticed — a number is a copy of a position, and it goes stale the next time the queue moves.

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
the mode, or the instructions — and one arm cannot say which. **The *A/B that says whether the rules
do anything* item below is now the measurement that matters most.**

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
twin reads **100 %** of it. This one reads **7.7 %** — 20 309 tokens, re-measured 2026-08-08 with the
`MANGLED` grader, edge within 500 tokens — and where the twin's failures were the server refusing,
this one's are the model answering wrong. **Post-training, not architecture, decided the usable
window.** A–K: 2 pass, 7 fail, with pathologies of its own — invented URLs that it then fetches,
empty responses after doing the reading, and a parent that contradicted its own sub-agent.

**Its two wrong answers either side of the edge are not the same failure**, which is worth more than
the percentage: below it the model restates the task and answers correctly; at 20 582 and 25 139 it
answers the literal string `<answer>marker</answer>`. It has stopped retrieving the marker and
started echoing the SHAPE of the question — the instruction survives where the content does not.

**A community fine-tune was tested and it separates the two purchases, 2026-08-08.**
`cybertruck32489/Jamba-Reasoning-3B-Agent-v1` carries an empty auto-generated card, so running it
was the only way to learn what it holds: its usable window is **85 452 tokens against its base's
20 309 — 4.2×** — and it scores **1 of 9** on A–K where the base scored 2. Someone trained long
context and wrote "Agent" on the box. It also **fabricated a `<tool_response>` block** in its own
output, at the exact shape the harness produces, with an invented exit code — see the *forged tool
result* item.
`results/jamba-reasoning-3b-agent-v1.md`.

**`squ11z1/gpt-oss-nano` is downloaded, fits, and is fast — 2026-08-08.** Its `config.json` is
`openai/gpt-oss-20b`'s with `num_local_experts` 12 instead of 32 and no MXFP4; LM Studio labels it
`12x2.4B`. At Q4_K_M it **loads its full declared 131 072** (6.36 GiB of weights, 3.0 GiB of cache —
12 of 24 layers are full attention, the rest capped at a 128-token window) and generates at **68.9
tok/s** at 6.8 k of prompt, **62.9** at 27 k.

**And the three-cell throughput test found something that changes the verdict on the parent.** Cell B
— nano forced to the SAME partial offload as the 20b — generates **15.8 tok/s**, slower than the
20b's 19.1 in that configuration. Holding the model constant and spilling costs 4.4–5.9×; holding the
spill constant and doubling the parameters costs nothing. **It is the spill that costs, not the
size**, so `gpt-oss-20b` is *"not on this card"* rather than *"not this model"*. `--gpu max` on a
model that does not fit **dies at 75 % rather than falling back** — partial offload is a ratio
somebody configures. `results/gpt-oss-nano.md` has the table and the settings beside each number.

**Nothing about its QUALITY is measured yet**, and the prior is poor: 131 072 is YaRN 32× from a 4096
native window, which is precisely the declared-versus-usable gap probe G exists to find.

## The queue, in order
1. **Probe G on `squ11z1/gpt-oss-nano`, then A–K.** It fits and it is fast (see above); what is
   unmeasured is whether it is any good. Its 131 072 is **YaRN 32× from a 4096 native window**, so the
   declared-versus-usable gap is the whole question — `lfm2.5` reads 66 % of what it loads and the
   Jamba twins read 100 % and 7.7 % from identical architectures. Under the selection rule it has to
   beat `qwen3.5-9b-deepseek-v4-flash`: 99.7 % of 128 000, 10 of 11. If probe G comes back short,
   A–K need not run.

2. **The forged tool result is NOT an OpenFox vulnerability — checked, 2026-08-08.**
   `Jamba-Reasoning-3B-Agent-v1` wrote a complete `<tool_response>` block into its own assistant
   text, right shape, invented exit code, for a command it never ran. The question that raised was
   whether the server ingests it. **It does not**: `grep -rn "tool_response" src/` returns nothing,
   and a tool result reaches the model only as a message with `role: 'tool'` and a `toolCallId`,
   built by the dispatcher (`src/server/events/fold-messages.ts`, read back in
   `src/server/ws/protocol.ts:64`). The forged block is inert text.
   **What remains is a READING hazard, and it is this kit's problem rather than the server's.**
   Probes A, C, E, F and K are graded by a human reading a transcript, and a fabricated tool result
   sits in that transcript looking exactly like a real one. It nearly graded as real here. So: when
   a transcript shows a tool result, check it came from a `[tool]` line the runner printed — the
   runner prints dispatched calls, and the model's prose is not one.

3. **Add a per-turn watchdog to the runner, and this one IS a defect.** Probe C hung for twelve
   minutes with the session reporting `isRunning: true` while LM Studio sat IDLE and the assistant
   message was empty — a model that leaks control tokens can stall a turn that has already
   finished. `isRunning` is cleared by a `running.changed` event in
   `src/server/chat/orchestrator.ts:246`, so the hang means that path was never reached. Two
   separate fixes: the server should not be able to hold a turn open with no generation running,
   and `run-probe.py` should report **STALLED** and move on rather than waiting out its whole
   timeout. The runner half is cheap and is what unblocks the queue.

4. **`ai21labs_ai21-jamba2-3b` is MEASURED and it is not an agent. Nothing left to run on it
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

5. **Re-run probe C on `lfm2.5-2.6b`.** It is the only one still unscored, and the reason was the
   runner rather than the model: it returned as soon as `isRunning` went false, which is before the
   final text commits, so every answer landed against the following question. Fixed — but the fix is
   unproven, and C is the probe the whole kit exists for.

6. **The two questions the rules exist to answer, and they are one run.** Does the model call
   `load_skill("regles-agent")` before working on a repository, unprompted — the instruction is
   deliberately unconditional — and once loaded, does it quote the skill or invent it? The second has
   a computed key: ask for the `git add -A` rule, which is in `SKILL.md` and **not** in the system
   prompt, and for a branch-naming rule, which is in neither. Inventing the second is the failure
   that matters.

7. **The A/B that says whether the rules do anything.** Re-run **B, C and E** on
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

8. **Probe K is the EVAL of truncation-recovery, and it needs a third arm.** With RTK on,
   `lfm2.5-2.6b` answered 205 against a true 17 587. Two arms are still missing, and they answer
   different questions:

   - **RTK off** — the gap between the two answers is what the filter costs in correctness against
     the tokens it saves. A model that gives the same number both times counted instead of reading.
   - **RTK on, and grade the TRAJECTORY rather than the number.** Three outcomes, kept apart:
     *(a)* answered from truncated output without noticing; *(b)* noticed the `+N more` marker and
     recovered — followed the printed `tail`, or re-ran under `rtk proxy`, or stopped piping into
     `wc -l`; *(c)* noticed and said so without recovering. Only (b) is the capability. **(a) is
     what every model here has done so far**, which is why the ruling above exists.

   Record which of the three, not just the count. A right number reached through (a) is luck.

9. **`prism-ml/bonsai-27b`: throughput, not depth.** Its ladder stopped at a client timeout, not a
   limit — loaded context 126 720, run stopped at 64 000. But it took 317 s at 32 000 where the 9 B
   takes 45 s, so what decides whether it is usable is tokens per second at a fixed context. Measure
   that first. **It also JIT-loads at 8.6 GiB** when anything addresses it, so unload it afterwards.

10. **Probe L on every model already measured** — the new capability probe (`PROBES.md` §L). It is
   three arithmetic questions with exact answers: a yaw-rotated box's AABB, a triangle's unit normal
   and area, a silhouette width. **It exists because the point of this kit is a `.catz` shape genre
   that does not exist yet**, and a model that cannot normalise a cross product cannot author or
   review a parametric solid however honest it is. Cheap — no repository, no window, no tools
   needed — so it runs on `lfm2.5-2.6b` and `qwen3.5-9b-deepseek-v4-flash` in minutes and says
   whether the small end of the range is usable for geometry content at all. Record whether the
   answer was computed, tool-called, or asserted; the third is untrustworthy even when right.

11. **The long-context candidates, and what has to be checked before downloading any of them.**
   The shortlist below came from a chat answer, so **treat every line as a claim until the repo says
   it**: the trap is a plausible spec for a model that does not exist under that name.

   | Candidate                          | Status of the claim                                                                                                                                                  | What decides it here                                                                                                                                                                                                                                                                                                                                                                                         |
   | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
   | `ai21labs/AI21-Jamba2-3B`          | **DOWNLOADED AND LOADED** — the GGUF question is answered: `bartowski/ai21labs_AI21-Jamba2-3B-GGUF`, Q4_K_M, 1.86 GB. See the *`ai21labs_ai21-jamba2-3b` is MEASURED* item and `results/ai21labs-jamba2-3b.md` | **Loaded 262 144 = declared, 3 342 MiB of VRAM**, matching the 0.26 GiB cache predicted from `config.json`. Only its honesty and its tool use are still unmeasured                                                                                                                                                                                                                                           |
   | `Qwen/Qwen3-30B-A3B-Instruct-2507` | **Verified**: 262 144 native, 30.5 B total / 3.3 B active, 128 experts 8 active, 48 layers, 4 KV heads, strong tool calling                                          | **Does not fit this box at its window.** MoE saves compute, not memory: all 30.5 B of weights must be resident (~18 GB at Q4) and the KV cache is a dense 48-layer one, ~96 KiB/token — **24 GiB at 256k, 12 GiB at 128k**. Against 12 GB of VRAM and 31 GB of RAM, 18 + 12 is the whole machine. Worth measuring only at a short window, and then it is competing with the 9 B that already scores 10 of 11 |
   | "Ministral 3 3B Instruct, 256k"    | **Unverified — and the number is suspect.** Mistral's published Ministral 3B is a 128k model                                                                         | Find the actual repo before planning a run. If the 256k variant does not exist, this line is a hallucinated spec and should be deleted rather than carried                                                                                                                                                                                                                                                   |
   | `amd/Instella-3B-Long-Instruct`    | **Unverified**                                                                                                                                                       | Same: confirm the repo, the context, and whether it tool-calls at all before it costs a download                                                                                                                                                                                                                                                                                                             |

   **`openai/gpt-oss-20b` was costed from its `config.json` on 2026-08-08 and NOT downloaded.**
   Recorded so nobody re-litigates it from a video. 21 B total / 3.6 B active, 24 layers alternating
   strictly `sliding_attention` / `full_attention`, so **12 full-attention layers** and 12 capped at a
   128-token window; GQA with 8 KV heads × 64 head_dim. **The cache is cheap** — 24 KiB/token, 3.0 GiB
   at its full 131 072, 0.75 GiB at 32 k. **The WEIGHTS are what fails, and quantisation is not a
   lever here**: `unsloth/gpt-oss-20b-GGUF` runs 11.47 GB at Q2_K to 12.04 GB at Q6_K — **0.57 GB
   across four bits**, because the bulk is already MXFP4 experts that llama.cpp leaves alone. A
   10.7 GiB floor on an 11.2 GiB card leaves nothing for a cache at any useful depth, so full offload
   is out and partial offload is a throughput question `prism-ml/bonsai-27b` has already answered
   badly. **And it buys no context**: 131 072 is the same order as qwen's 128 000, which is measured
   at 99.7 % — while `initial_context_length` is **4096**, extended 32× by YaRN, which is precisely
   the declared-versus-usable gap this kit exists to measure. Under the selection rule above it is a
   quality bet at the same context, for the price of the whole card.

   **The order that wastes the least: confirm the GGUF, compute the cache from `config.json`, then
   download.** Jamba2-3B is the only candidate whose architecture makes 256k cheap on this card, so
   it is the one worth the check.

12. **Or fine-tune `lfm2.5-2.6b` instead — and note what that would and would not fix.** It already
   scores 8/1/2 and loads its full 128 000. Its measured gap is **comprehension**, not window: it
   uses 66.2 % of what it loads, where the 9 B uses 99.7 %. Fine-tuning changes behaviour — refusal
   phrasing, tool discipline, format adherence — and **a fine-tune does not extend the window it can
   actually reason across**; that is architecture and training length. So it is the right lever for
   the probes it fails on behaviour, and the wrong one for the 84 707 ceiling. The *probe L on every
   model* item says whether the arithmetic is there to build on before any of this is worth doing.

   **The named target is truncation-recovery** (the ruling above): a model that sees `+N more`,
   stops, and re-runs under `rtk proxy` instead of answering from the window it was handed. That is
   behaviour and nothing else — the marker is already on the screen, so no amount of context would
   have helped, which is exactly why it is the right thing to fine-tune rather than the window.
   Probe K's arm (b) is the acceptance test, and today the training set is empty: every model
   measured here is at (a).

13. **Re-measure a window whenever the machine changes.** A new LM Studio version, a driver update,
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
