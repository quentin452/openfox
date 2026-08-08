#!/usr/bin/env python3
"""Run one probe against a running OpenFox, from a terminal.

The kit's README says to open a fresh session and paste the probes one at a time. That is a
human in a browser, which makes a probe run expensive enough to skip and impossible to repeat
after a settings change — the exact comparison `NEXT.md` item 2 asks for.

OpenFox already answers everything a runner needs over HTTP: create a session, pin its model,
post a message, read back the messages *and the tool calls*. So this drives it.

**It prints the tool calls, and that is the point.** Probes A, C, E and F are not graded on the
answer alone: "did it call a tool before answering" and "did the sub-agent call actually happen"
are the questions, and the transcript is the only place they are answered. A runner that printed
just the final text would grade the same failure as a pass.

    ./run-probe.py --repo ~/Documents/GitHub/openfox --model zai-org/glm-4.6v-flash \\
        "How many lines exactly are there in src/server/ws/server.ts?"

    ./run-probe.py --session <id> "Which tool call put it there?"   # same session, next turn

Every probe wants a FRESH session unless it is a follow-up (probe C's second question) or a
deliberate later turn (probe J). `--session` is how those two say so.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_HOST = "http://localhost:10369"


def call(host, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{host}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path} -> HTTP {e.code}: {e.read().decode()[:400]}")
    except urllib.error.URLError as e:
        sys.exit(f"cannot reach OpenFox at {host}: {e.reason}\nis it running?")
    return json.loads(raw) if raw else {}


def project_for(host, workdir):
    """The project whose workdir is this repository, created if there is none."""
    workdir = os.path.realpath(os.path.expanduser(workdir))
    for project in call(host, "GET", "/api/projects")["projects"]:
        if os.path.realpath(project["workdir"]) == workdir:
            return project
    created = call(
        host,
        "POST",
        "/api/projects",
        {"name": os.path.basename(workdir), "workdir": workdir},
    )
    return created.get("project", created)


def model_exists(host, provider_id, model):
    """Refuse a model the provider does not offer, rather than measuring a silent fallback."""
    for provider in call(host, "GET", "/api/providers")["providers"]:
        if provider["id"] != provider_id:
            continue
        return any(m["id"] == model for m in provider.get("models", []))
    return False


def lmstudio_provider(host):
    providers = call(host, "GET", "/api/providers")["providers"]
    for provider in providers:
        if provider.get("backend") == "lmstudio":
            return provider
    sys.exit("no LM Studio provider configured in OpenFox")


def loaded_context(model):
    """What LM Studio actually loaded, read while the model is resident.

    Declared is not loaded (`README.md`), and an idle model is unloaded on a TTL and takes the
    answer with it — so this is read at the moment of the run or not at all.
    """
    try:
        with urllib.request.urlopen("http://localhost:1234/api/v0/models", timeout=5) as r:
            models = json.load(r).get("data", [])
    except Exception:
        return None
    for entry in models:
        if entry.get("id") == model:
            return entry.get("state"), entry.get("loaded_context_length"), entry.get("max_context_length")
    return None


def text_of(part):
    if isinstance(part, str):
        return part
    if isinstance(part, dict):
        return part.get("text") or part.get("content") or ""
    return ""


def render(message):
    """One message, as a grader needs to see it: who spoke, what tool ran, what came back."""
    kind = message.get("type") or message.get("role") or "?"
    lines = []

    # Tool calls arrive as a list on the assistant message, each with its own result. Printing them
    # is the point: probes A, C, E and F are graded on whether a tool ran at all, and on whether the
    # parent's account matches what came back.
    for call in message.get("toolCalls") or []:
        args = json.dumps(call.get("arguments"), ensure_ascii=False)[:160]
        result = call.get("result") or {}
        output = result.get("output")
        size = f"{len(output)} chars" if isinstance(output, str) else "no output"
        lines.append(f"  [tool] {call.get('name')} {args} -> {size}")

    name = message.get("name") or message.get("toolName") or (message.get("tool") or {}).get("name")
    if name:
        args = message.get("args") or message.get("input") or (message.get("tool") or {}).get("args")
        rendered = json.dumps(args, ensure_ascii=False)[:300] if args is not None else ""
        lines.append(f"  [tool] {name} {rendered}")

    content = message.get("content") or message.get("text") or ""
    body = content if isinstance(content, str) else "".join(text_of(p) for p in content)
    body = body.strip()
    if body:
        lines.append("\n".join(f"  {line}" for line in body.splitlines()))

    if not lines:
        lines.append(f"  {json.dumps(message, ensure_ascii=False)[:300]}")
    return f"[{kind}]\n" + "\n".join(lines)


def this_turn(state, mark):
    """The messages THIS probe produced. Everything before `mark` belongs to an earlier one."""
    return state.get("messages", [])[mark:]


def turn_shape(state, mark):
    """A fingerprint of how far this turn has got, for the stall watchdog.

    Message count and total text length, so a turn that is streaming, calling a tool or thinking
    all read as movement — and only a turn where nothing at all is happening looks still.
    """
    messages = this_turn(state, mark)
    return (len(messages), sum(len(str(m.get("content") or "")) for m in messages))


def answered(state, mark):
    """Whether THIS probe has committed assistant text.

    **Scoped to this turn on purpose.** Asking whether the session's last message is assistant text
    answers yes on the previous probe's answer, which is how a whole run comes to be graded one
    question out of step.
    """
    return any(
        m.get("role") == "assistant" and isinstance(m.get("content"), str) and m["content"].strip()
        for m in this_turn(state, mark)
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("probe", help="the probe text, as written in PROBES.md")
    ap.add_argument("--repo", help="target repository (a project is created if there is none)")
    ap.add_argument("--session", help="continue this session instead of opening a fresh one")
    ap.add_argument("--model", help="pin the model, e.g. zai-org/glm-4.6v-flash")
    ap.add_argument("--mode", default="builder", help="agent mode (default: builder — it has read_file and load_skill)")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--timeout", type=int, default=900, help="seconds to wait for the turn (default 900)")
    ap.add_argument(
        "--settle",
        type=int,
        default=30,
        help="seconds to wait for THIS probe's answer after isRunning goes false (default 30)",
    )
    ap.add_argument(
        "--stalled-after",
        type=int,
        default=240,
        help=(
            "seconds with no change at all while the session still claims to be running, before "
            "this reports STALLED and moves on (default 240). Deliberately larger than the "
            "server's own 120 s idle timeout, so the server gets to produce a real error first "
            "and this only speaks when it did not"
        ),
    )
    args = ap.parse_args()

    host = args.host

    if args.session:
        session_id = args.session
        before = call(host, "GET", f"/api/sessions/{session_id}?full=true")
    else:
        if not args.repo:
            sys.exit("--repo is required unless --session continues an existing one")
        project = project_for(host, args.repo)
        created = call(host, "POST", "/api/sessions", {"projectId": project["id"], "title": "probe"})
        session_id = created["session"]["id"]
        call(host, "PUT", f"/api/sessions/{session_id}/mode", {"mode": args.mode})
        before = {"messages": []}

    if args.model:
        provider = lmstudio_provider(host)
        if not model_exists(host, provider["id"], args.model):
            sys.exit(f"{args.model} is not a model {provider['name']} offers — refusing to measure a fallback")
        call(host, "POST", f"/api/sessions/{session_id}/provider", {"providerId": provider["id"], "model": args.model})

    session = call(host, "GET", f"/api/sessions/{session_id}")["session"]
    model = session.get("providerModel")
    resident = loaded_context(model)
    print(f"session {session_id}  mode={session.get('mode')}  model={model}")
    if resident:
        state, loaded, declared = resident
        print(f"LM Studio: state={state} loaded_context={loaded} declared={declared}")
    else:
        print("LM Studio: not reporting this model — declared-vs-loaded unknown for this run")
    print(f"probe: {args.probe}\n")

    mark = len(before.get("messages", []))
    started = time.time()
    call(host, "POST", f"/api/sessions/{session_id}/message", {"content": args.probe})

    # The session flips to running asynchronously; a poll that only checked isRunning would see
    # the pre-flip false and call the turn finished before it began.
    seen_running = False
    verdict = None
    last_shape = turn_shape(state, mark)
    last_change = started

    while True:
        time.sleep(2)
        state = call(host, "GET", f"/api/sessions/{session_id}?full=true")
        running = state["session"]["isRunning"]
        seen_running = seen_running or running
        now = time.time()
        elapsed = now - started

        shape = turn_shape(state, mark)
        if shape != last_shape:
            last_shape, last_change = shape, now

        if seen_running and not running:
            # `isRunning` flips before the final assistant text is committed, so returning here
            # captures the turn without its answer — and the answer then shows up at the top of the
            # NEXT probe's output, which silently misaligns a whole run. Measured: an eleven-probe
            # session where every answer was attributed to the following question.
            #
            # **Two things this used to get wrong, and the second is why the race was thought
            # closed when it was not.** It waited a fixed five polls and then gave up quietly; and
            # it inspected `messages[-1]`, the last message in the SESSION, which in a continued
            # session is the PREVIOUS probe's answer — already committed, already non-empty, so the
            # wait ended immediately and the race was never actually waited out. Only messages from
            # this probe count, and running out of patience is a verdict rather than a silence.
            deadline = now + args.settle
            while not answered(state, mark) and time.time() < deadline:
                time.sleep(2)
                state = call(host, "GET", f"/api/sessions/{session_id}?full=true")
            if not answered(state, mark):
                verdict = (
                    f"NO ANSWER — the turn ended and no assistant text arrived within {args.settle}s. "
                    "Do NOT grade this as a model failure and do NOT read the next probe's output as "
                    "this one's answer."
                )
            break

        if running and now - last_change > args.stalled_after:
            # The server thinks a turn is in flight and nothing has moved. Measured once at twelve
            # minutes with the provider idle and the assistant message empty. Waiting out the whole
            # --timeout buys nothing: what is being measured has already stopped.
            verdict = (
                f"STALLED after {elapsed:.0f}s — the session still reports isRunning and nothing has "
                f"changed for {args.stalled_after}s. This measures the harness, not the model: "
                "leave the probe unscored."
            )
            break

        if elapsed > args.timeout:
            verdict = f"TIMEOUT after {elapsed:.0f}s — a client timeout is not a model limit (PROBES.md §G)"
            break

        if not seen_running and elapsed > 60:
            verdict = "the session never started running — is a model loaded?"
            break

    for message in state["messages"][mark:]:
        print(render(message))

    if verdict:
        print(f"\n{verdict}")
    print(f"\n{time.time() - started:.1f}s  session {session_id}")


if __name__ == "__main__":
    main()
