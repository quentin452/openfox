#!/usr/bin/env python3
"""Probe M — can the model BUILD in a language with specific verbs, graded by a compiler?

**This is the probe that needs no human, and that is the whole point.** Five of A–K are graded by
somebody reading a transcript, which is slow and which is where a forged tool result nearly got
graded as real. Here the answer is a `.catz` file, and `catzc` already refuses one that is wrong:
the file parses, resolves against the declaration table, reads into a mass and reprints byte for
byte — or it does not. Nothing is graded by eye.

**And it measures the thing that actually matters for this project.** A generalist coding benchmark
asks whether a model can write software; the question here is narrower and answerable: can it write
CONTENT in a language whose whole specification and whole corpus fit in about 8 600 tokens. Window
is not the criterion — that much has been measured — and neither is parameter count.

**The score is tiered rather than pass/fail**, because the failures are different problems:

    parses   → the lexer accepted it. Below this the model is not writing the language at all.
    resolves → every word it wrote exists, in a genre that may hold it.
    reads    → the shape is coherent: solids inside parts, arities right.
    prints   → byte-identical on the round trip, which is the format's founding contract (§1.4).
    gated    → the whole corpus still passes with it in, which is the real bar.

Usage:  ./catz-gate.py --engine ~/Documents/GitHub/CatzEngine [--model <id>]
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

LM_STUDIO = "http://localhost:1234"
#: Written into the corpus and removed again. Named so it cannot collide with anything authored.
SUBJECT = "catz.prop.probe_m"


def section_seven(format_md: Path) -> str:
    """`FORMAT.md` §7, read out of the document rather than paraphrased here.

    A brief that restated the rules would be a second copy of the specification, and it would go
    stale the first time the language grew — which is the failure this repository keeps recording.
    """
    text = format_md.read_text()
    start = text.index("## 7. Creatures and props")
    end = text.index("## 8.", start)
    return text[start:end].strip()


def palette_inks(palette: Path) -> list[str]:
    """The ink names the subject may use, taken from the palette file it will draw from."""
    return re.findall(r"^\s*ink\s+([a-z][a-z0-9_]*)", palette.read_text(), re.MULTILINE)


def ask(model: str, brief: str, timeout: int) -> str:
    request = urllib.request.Request(
        LM_STUDIO + "/api/v0/chat/completions",
        data=json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": brief}],
                "max_tokens": 4096,
                "temperature": 0.0,
                "stream": False,
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.load(response)
    choice = body["choices"][0]["message"]
    return choice.get("content") or choice.get("reasoning_content") or ""


def written_file(answer: str) -> str | None:
    """The fenced block the model produced, or `None` when it produced prose instead.

    **Not graded as a failure of the language.** A model that explains a `.catz` file instead of
    writing one has failed to follow the instruction, which probe H already measures; this reports
    it apart so the two are not confused.
    """
    fenced = re.findall(r"```(?:catz)?\n(.*?)```", answer, re.DOTALL)
    return fenced[0] if fenced else None


def grade(engine: Path, body: str) -> tuple[dict[str, bool], str]:
    """Write the file into the corpus, ask `catzc`, and take it out again."""
    target = engine / "content" / "catz" / "prop" / "probe_m.catz"
    if target.exists():
        raise SystemExit(f"{target} already exists — refusing to overwrite an authored file")

    tiers = {"parses": False, "resolves": False, "reads": False, "prints": False, "gated": False}
    detail = ""
    try:
        target.write_text(body if body.endswith("\n") else body + "\n")
        # One command answers the first four tiers: `roundtrip` walks the whole corpus, binds every
        # file and prints it back. Its diagnostic names which stage refused.
        walked = subprocess.run(
            ["cargo", "test", "-q", "-p", "catz-gates", "--test", "roundtrip"],
            cwd=engine,
            capture_output=True,
            text=True,
            timeout=900,
        )
        # **Matched on the WHOLE output, sliced only for display.** Searching a truncated view
        # for a marker is the failure probe K exists to measure, and this harness committed it:
        # the diagnostic naming the refusal sat above the 1200-character tail being searched.
        full = walked.stdout + walked.stderr
        detail = full[-1200:]
        if walked.returncode == 0:
            tiers.update(parses=True, resolves=True, reads=True, prints=True)
            checked = subprocess.run(
                ["cargo", "run", "-q", "-p", "catzc", "--", "check"],
                cwd=engine,
                capture_output=True,
                text=True,
                timeout=1800,
            )
            # `clean-tree` refuses an uncommitted file, and this one is deliberately uncommitted —
            # so the gate is every OTHER gate passing, which is what the count says.
            tiers["gated"] = "clean-tree   FAILED" in checked.stdout and "gate(s) ok" not in checked.stdout and checked.stdout.count("FAILED") == 1
            full = checked.stdout + checked.stderr
            detail = full[-1200:]
        else:
            # **The stage is read from the FAILING TEST'S NAME, not from the prose of a
            # diagnostic.** Two earlier versions of this matched on wording and got it wrong twice:
            # a message the harness did not anticipate was scored as three passing tiers. The test
            # names come from the engine and change with it, which is the same "ask the source, do
            # not guess its words" the whole repository is built on.
            failed = set(re.findall(r"^\s+(\w+)$", full, re.MULTILINE))
            by_stage = {
                "parses": "the_corpus_exercises_every_syntactic_element",
                "resolves": "every_ink_named_by_the_corpus_resolves",
                "reads": "every_creature_and_prop_in_the_corpus_reads_into_a_mass",
                "prints": "every_committed_file_prints_back_byte_for_byte",
            }
            # A file that does not LOAD fails every one of them at once, because `read::strict`
            # runs first: that is the lexer or the resolver, and nothing above it was reached.
            everything = all(name in failed for name in by_stage.values())
            for stage, name in by_stage.items():
                tiers[stage] = not everything and name not in failed
            if everything:
                tiers["parses"] = "is not a declaration" not in full and "searched:" not in full
    finally:
        target.unlink(missing_ok=True)
    return tiers, detail


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", required=True, type=Path, help="the CatzEngine checkout")
    ap.add_argument("--model", default=None, help="defaults to whatever LM Studio has loaded")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    engine = args.engine.expanduser()
    spec = section_seven(engine / "docs" / "FORMAT.md")
    inks = palette_inks(engine / "content" / "catz" / "palette" / "world.catz")

    brief = (
        "Here is the whole specification of the `prop` genre of a content language called `.catz`.\n\n"
        f"{spec}\n\n"
        "Now write ONE complete `.catz` file describing a prop: a wooden crate.\n\n"
        "Requirements:\n"
        f"- Its subject line must be exactly: prop {SUBJECT}\n"
        "- It must begin with the headers `use draw.*`, `use creature.*` and "
        "`from catz.palette.world`.\n"
        f"- Every `ink=` you write must be one of these, and nothing else: {', '.join(inks)}\n"
        "- A prop must NOT declare `ground`.\n"
        "- Two spaces per indent level. Solids are indented under the `part` that holds them.\n\n"
        "Answer with the file and nothing else, in a single ```catz code block."
    )

    model = args.model
    if model is None:
        with urllib.request.urlopen(LM_STUDIO + "/api/v0/models", timeout=10) as response:
            loaded = [m for m in json.load(response)["data"] if m.get("state") == "loaded"]
        if not loaded:
            raise SystemExit("no model is loaded")
        model = loaded[0]["id"]

    print(f"probe M against {model} — brief is {len(brief)} chars, ~{len(brief) // 4} tokens")
    answer = ask(model, brief, args.timeout)
    body = written_file(answer)
    if body is None:
        print("  NO FILE — the answer holds no fenced block. It described instead of writing:")
        print("  " + answer.strip()[:200].replace("\n", "\n  "))
        sys.exit(1)

    print(f"  produced {len(body.splitlines())} lines")
    tiers, detail = grade(engine, body)
    for stage, ok in tiers.items():
        print(f"  {stage:<9} {'ok' if ok else 'NO'}")
    if not all(tiers.values()):
        print("\n--- what refused it ---")
        print(detail.strip()[-900:])
        print("\n--- what it wrote ---")
        print(body.strip())


if __name__ == "__main__":
    main()
