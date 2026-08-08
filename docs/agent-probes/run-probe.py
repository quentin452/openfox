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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("probe", help="the probe text, as written in PROBES.md")
    ap.add_argument("--repo", help="target repository (a project is created if there is none)")
    ap.add_argument("--session", help="continue this session instead of opening a fresh one")
    ap.add_argument("--model", help="pin the model, e.g. zai-org/glm-4.6v-flash")
    ap.add_argument("--mode", default="builder", help="agent mode (default: builder — it has read_file and load_skill)")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--timeout", type=int, default=900, help="seconds to wait for the turn (default 900)")
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
    while True:
        time.sleep(2)
        state = call(host, "GET", f"/api/sessions/{session_id}?full=true")
        running = state["session"]["isRunning"]
        seen_running = seen_running or running
        elapsed = time.time() - started
        if seen_running and not running:
            break
        if elapsed > args.timeout:
            print(f"TIMEOUT after {elapsed:.0f}s — a client timeout is not a model limit (PROBES.md §G)")
            break
        if not seen_running and elapsed > 60:
            print("the session never started running — is a model loaded?")
            break

    for message in state["messages"][mark:]:
        print(render(message))

    print(f"\n{time.time() - started:.1f}s  session {session_id}")


if __name__ == "__main__":
    main()
