#!/usr/bin/env python3
"""Find the exact token at which a model stops finding the marker.

Probe G used to be a ladder — 8 000, 32 000, 64 000, 128 000, 200 000 — and a ladder answers a
different question than the one anybody has. "Passed 64 000, refused 128 000" is a **bracket two
rungs wide**: the real edge is somewhere in a 64 000-token gap, and every rung below the edge is a
run spent confirming what the previous rung already said.

So this starts at the ceiling the backend actually loaded and **bisects**. The first probe is the
one that matters — the largest depth the model could possibly answer — and each one after it halves
what is left unknown. Reaching a ±500-token answer takes about eight requests instead of five, and
the five did not produce an answer at all.

    ./find-window.py --model lfm2.5-2.6b
    ./find-window.py --model lfm2.5-2.6b --tolerance 200 --note "--gpu max"

**The ceiling is read, not assumed.** LM Studio fits the KV cache to the VRAM it has and loads a
smaller window than the model declares, silently — so the search starts from
`loaded_context_length` on a resident model, and refuses to run against one that is not loaded,
because an idle model unloads on a TTL and takes the answer with it.

**Four outcomes, kept apart, because they have different fixes** (`PROBES.md` §G):

* `PASS`    — the marker came back. The model read that much.
* `WRONG`   — it answered something else. That is a comprehension limit.
* `REFUSED` — HTTP 400 in a second or two. That is the **server's** context limit and the model
  never saw the text. Not the same finding, and not the same fix.
* `TRUNCATED` — it ran out of *output* tokens before saying anything. **That is this script's cap,
  not the model's window**, and calling it a failure would report a limit that belongs to the
  runner. It is here because a thinking model spends output tokens on reasoning before it answers:
  the first version of this script asked for 64 and graded only `content`, which scored LFM2.5
  `WRONG` at every depth while its answer sat in `reasoning_content`, finished by `length`. A
  reasoning field counts — finding the marker there is proof the model read the text, which is the
  only thing probe G asks.

The marker is generated here and checked here, so it cannot be retyped wrong — the failure that
made a correct model look broken on the kit's first real run.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

LM_STUDIO = "http://localhost:1234"

# The filler `ground-truth.sh` writes, reproduced exactly so a bisected window and a laddered one
# are the same measurement. Change one and the two stop being comparable.
FILLER = "Filler line %d: this sentence exists to occupy context and says nothing at all."
PREAMBLE = "Filler text follows. Read it all; a marker is hidden inside."
QUESTION = "What is the marker string in the text above? Answer with the marker only."


def needle(chars, marker):
    """Filler of about `chars` characters with the marker at its midpoint."""
    lines = [PREAMBLE]
    written = 0
    placed = False
    n = 0
    while written < chars:
        n += 1
        line = FILLER % n
        if not placed and written >= chars / 2:
            lines.append(f"The marker is: {marker}")
            placed = True
        lines.append(line)
        written += len(line) + 1
    if not placed:
        lines.append(f"The marker is: {marker}")
    return "\n".join(lines)


def resident(host, model):
    """(loaded_context_length, declared) for a model that is loaded right now, or exit."""
    try:
        with urllib.request.urlopen(f"{host}/api/v0/models", timeout=10) as r:
            entries = json.load(r).get("data", [])
    except urllib.error.URLError as e:
        sys.exit(f"cannot reach LM Studio at {host}: {e.reason}")
    for entry in entries:
        if entry.get("id") != model:
            continue
        if entry.get("state") != "loaded":
            sys.exit(
                f"{model} is not loaded — declared is not loaded, and an idle model takes the\n"
                f"answer with it. Load it first:  ./lmstudio.sh load {model} <ctx> max"
            )
        return entry.get("loaded_context_length"), entry.get("max_context_length")
    sys.exit(f"{model} is not a model this server knows")


def ask(host, model, text, timeout, max_tokens):
    """One probe. Returns (verdict, real_prompt_tokens, seconds, detail)."""
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": f"{text}\n\n{QUESTION}"}],
            "temperature": 0,
            "max_tokens": max_tokens,
        }
    ).encode()
    req = urllib.request.Request(
        f"{host}/v1/chat/completions", data=body, headers={"Content-Type": "application/json"}
    )
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            answer = json.load(r)
    except urllib.error.HTTPError as e:
        # The one that is NOT the model getting it wrong: the server refused the request because it
        # is longer than the context it loaded, and nothing was read.
        return "REFUSED", None, time.time() - started, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return "REFUSED", None, time.time() - started, str(e.reason)
    except TimeoutError:
        return "TIMEOUT", None, time.time() - started, f"no reply in {timeout}s"

    choice = answer["choices"][0]
    message = choice["message"]
    # Both fields, and the reasoning one is not a consolation prize: a model that names the marker
    # while thinking has read the text, which is the whole of what this probe asks.
    said = (message.get("content") or "").strip()
    thought = (message.get("reasoning_content") or "").strip()
    tokens = answer.get("usage", {}).get("prompt_tokens")
    if said:
        detail = said
    elif thought:
        detail = f"[reasoning] {thought}"
    else:
        detail = ""
    if not detail and choice.get("finish_reason") == "length":
        return "TRUNCATED", tokens, time.time() - started, "output cap reached before it said anything"
    return "answered", tokens, time.time() - started, detail


#: Verdicts that mean the model READ the text at that depth. `MANGLED` is one of them — see
#: `probe` for why it is graded apart and searched together.
READ = ("PASS", "MANGLED")


def probe(host, model, chars, timeout, index, max_tokens):
    marker = f"NEEDLE-{index}-{chars}"
    verdict, tokens, seconds, detail = ask(host, model, needle(chars, marker), timeout, max_tokens)
    if verdict == "answered":
        # **Case-insensitive, and the loosening is the kit's own stated intent.** Probe G asks one
        # thing: did the model READ that much text. A model that returns the marker lowercased has
        # read it — grading that WRONG measures its output formatting, not its window.
        # `ai21-jamba-reasoning-3b` answered `<needle-5-64225>` at 16 675 tokens where the marker is
        # `NEEDLE-5-64225`, and an exact match scored that a comprehension failure.
        #
        # MANGLED is kept APART from PASS rather than folded into it, because the two are different
        # findings: one model returns what it read, the other returns what it read after mangling
        # it, and a bisect that could not tell them apart would hide the second.
        if marker in detail:
            verdict = "PASS"
        elif marker.casefold() in detail.casefold():
            verdict = "MANGLED"
        else:
            verdict = "WRONG"
    shown = f"{tokens} tokens" if tokens else "never read"
    print(f"  {chars:>9,} chars  {verdict:<8} {shown:>14}  {seconds:6.1f}s  {detail[:60]!r}")
    return verdict, tokens


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True)
    ap.add_argument("--host", default=LM_STUDIO)
    ap.add_argument("--tolerance", type=int, default=500, help="stop when the bracket is this many tokens wide (default 500)")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per request (default 1800)")
    ap.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="output cap. Generous on purpose: a thinking model spends it on reasoning before it "
        "answers, and a cap that cuts it off measures the runner (default 1024)",
    )
    ap.add_argument("--note", default="", help="recorded beside the result — the offload setting, above all")
    args = ap.parse_args()

    loaded, declared = resident(args.host, args.model)
    print(f"{args.model}: declared {declared:,}, LOADED {loaded:,}" + (f"  [{args.note}]" if args.note else ""))
    if declared and loaded and declared != loaded:
        print(f"  the gap is the finding: LM Studio fit the KV cache to VRAM and loaded {loaded/declared:.1%} of what the model declares")

    # Characters, at the conservative 4-per-token `ground-truth.sh` uses. Start just under the
    # ceiling: the question and the answer need room too, and a first probe that is refused for
    # arithmetic rather than for capacity wastes the most expensive request of the run.
    high = int(loaded * 4 * 0.98)
    low = 0
    best_tokens = None
    index = 0

    print("\nceiling first, then halving what is left unknown:")
    index += 1
    verdict, tokens = probe(args.host, args.model, high, args.timeout, index, args.max_tokens)
    # MANGLED counts as READ for the search: the marker came back, in the wrong case. The edge this
    # bisect looks for is where the model stops finding it, not where it stops formatting it.
    if verdict in READ:
        print(f"\nusable window: {tokens:,} real tokens — the whole loaded context. Nothing to bisect.")
        return
    ceiling_verdict = verdict

    while high - low > args.tolerance * 4:
        mid = (low + high) // 2
        index += 1
        verdict, tokens = probe(args.host, args.model, mid, args.timeout, index, args.max_tokens)
        if verdict in READ:
            low, best_tokens = mid, tokens
        else:
            high = mid

    if best_tokens is None:
        print(f"\nno depth passed, down to {low:,} chars. The failure at the ceiling was {ceiling_verdict}.")
        return

    print(f"\nusable window: {best_tokens:,} real tokens (at {low:,} chars)")
    print(f"the edge is between that and the first {ceiling_verdict} above it, within {args.tolerance} tokens")
    print(f"of {loaded:,} loaded — {best_tokens / loaded:.1%}")


if __name__ == "__main__":
    main()
