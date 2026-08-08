#!/usr/bin/env bash
# Drive LM Studio from a terminal: load a model with a stated context and offload, and say what is
# actually loaded rather than what is configured.
#
# Why this exists: the settings page and the loaded model are two different facts. LM Studio fits
# the KV cache to available VRAM and loads a SMALLER window than the model declares, silently — a
# model declaring 262 144 loaded at 126 720 on this machine, and that stale number then travelled
# into a client's config and outlived the reason for it. Every command here reports what is loaded.
#
# Usage:
#   lmstudio.sh status                       what is loaded, at what context, and what it costs
#   lmstudio.sh load <model> [ctx] [gpu]     load explicitly; gpu is max|off|0..1 (default max)
#   lmstudio.sh estimate <model>             resource estimate without loading
#   lmstudio.sh unload                       unload everything
#   lmstudio.sh models                       what is on disk, and what the server offers
#
# `lms` is installed by `curl -fsSL https://lmstudio.ai/install.sh | bash` and is NOT put on PATH,
# so it is resolved rather than assumed.

set -uo pipefail

LMS=$(command -v lms 2>/dev/null || echo "$HOME/.lmstudio/bin/lms")
API=${LMSTUDIO_API:-http://localhost:1234}

[ -x "$LMS" ] || { echo "lms not found — looked on PATH and at $HOME/.lmstudio/bin/lms" >&2; exit 1; }

# `lms load` prints a progress spinner with carriage returns. Left alone it fills a terminal — and
# a log — with hundreds of redraw frames.
quiet() { "$LMS" "$@" 2>&1 | tr '\r' '\n' | grep -viE '^\s*$|Loading .*%|^\[\?25|^\[K'; }

vram() {
  command -v nvidia-smi >/dev/null 2>&1 || { echo "n/a"; return; }
  nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader | head -1
}

case "${1:-status}" in
  status)
    echo "server: $API"
    "$LMS" ps 2>/dev/null | grep -viE '^\s*$|waking up'
    echo "vram:   $(vram)"
    echo
    echo "what the server reports (declared vs loaded — the pair that matters):"
    curl -s --max-time 5 "$API/api/v0/models" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)["data"]
except Exception:
    print("  (server not answering)")
    raise SystemExit(0)
for m in data:
    if m.get("type") in ("llm", "vlm"):
        name = m["id"]
        state = m.get("state")
        declared = m.get("max_context_length")
        loaded = m.get("loaded_context_length")
        print("  %-34s state=%-11s declared=%s loaded=%s" % (name, state, declared, loaded))
'
    ;;

  load)
    model=${2:?usage: lmstudio.sh load <model> [ctx] [gpu]}
    ctx=${3:-}
    gpu=${4:-max}
    args=("$model" --gpu "$gpu" -y)
    [ -n "$ctx" ] && args+=(-c "$ctx")
    echo "loading $model (ctx=${ctx:-default} gpu=$gpu)"
    quiet load "${args[@]}"
    echo
    "$0" status
    ;;

  estimate)
    model=${2:?usage: lmstudio.sh estimate <model>}
    # Weights only, and LM Studio says LOW confidence on its own numbers. The KV cache is the part
    # that decides whether a context fits, and it is not in here — measure a real load for that.
    quiet load "$model" --estimate-only -y
    ;;

  unload)
    quiet unload --all
    echo "vram after: $(vram)"
    ;;

  models)
    "$LMS" ls 2>/dev/null | grep -viE 'waking up'
    ;;

  *)
    sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
