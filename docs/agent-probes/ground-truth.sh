#!/usr/bin/env bash
# Generate the answer key for docs/agent-probes/PROBES.md against a target repository.
#
# Usage: ground-truth.sh [TARGET_REPO] [OUT_DIR]
#          TARGET_REPO  defaults to the current directory
#          OUT_DIR      defaults to ./agent-probe-key
#
# Everything it prints is computed, not assumed. The point of the kit is that no answer in the key
# is something a person typed from memory.

set -euo pipefail

REPO=$(cd "${1:-.}" && pwd)
OUT=${2:-./agent-probe-key}
mkdir -p "$OUT"

command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
git -C "$REPO" rev-parse --git-dir >/dev/null 2>&1 || {
  echo "$REPO is not a git repository — the key needs tracked files to choose from" >&2
  exit 1
}

# ---------------------------------------------------------------------------
# Sizes of every tracked file, in ONE stat call.
#
# A `wc -c` per file plus a `head` that closes the pipe early is how the first version of this
# script died on a large repository: `head` exiting sends SIGPIPE to the loop feeding it, and
# `set -o pipefail` turns that into exit 141. Nothing selects with `head` below for that reason.
# ---------------------------------------------------------------------------
SIZES=$(git -C "$REPO" ls-files -z | (cd "$REPO" && xargs -0 stat -c '%s %n' 2>/dev/null) || true)
[ -n "$SIZES" ] || { echo "no tracked files found in $REPO" >&2; exit 1; }

# Pick the largest tracked text file inside a size band: big enough that its length is not
# guessable, small enough to paste. `awk` reads all of its input, so no early close.
pick_file() {
  local skip=$1 min=$2 max=$3
  printf '%s\n' "$SIZES" | awk -v skip="$skip" -v min="$min" -v max="$max" '
    {
      size = $1
      name = $0
      sub(/^[0-9]+ /, "", name)
      if (name == skip) next
      if (name ~ /\.(png|jpe?g|gif|ico|svg|pdf|zip|gz|woff2?|ttf|wasm)$/) next
      if (name ~ /(^|\/)(package-lock\.json|Cargo\.lock|yarn\.lock|pnpm-lock\.yaml)$/) next
      if (size < min || size > max) next
      if (size > best_size) { best_size = size; best = name }
    }
    END { if (best != "") print best }'
}

FILE_A=$(pick_file '' 2000 60000)
[ -n "$FILE_A" ] || { echo "no suitable tracked file found in $REPO" >&2; exit 1; }

FILE_A_LINES=$(wc -l <"$REPO/$FILE_A" | tr -d ' ')
FILE_A_BYTES=$(wc -c <"$REPO/$FILE_A" | tr -d ' ')
FILE_A_SHA=$(sha256sum "$REPO/$FILE_A" | cut -c1-16)

# A line from the middle, long enough that a paraphrase is obvious.
LINE_D_NUMBER=$(
  awk 'length($0) > 40 { print NR }' "$REPO/$FILE_A" | awk '{ a[NR]=$1 } END { print a[int(NR/2)+1] }'
)
LINE_D_NUMBER=${LINE_D_NUMBER:-1}
LINE_D_TEXT=$(sed -n "${LINE_D_NUMBER}p" "$REPO/$FILE_A")

# ---------------------------------------------------------------------------
# FILE_C: a real file the agent will NOT have read at the start of a session —
# something other than FILE_A and not the first thing an explorer lists.
# ---------------------------------------------------------------------------
FILE_C=$(pick_file "$FILE_A" 1500 400000)
FILE_C=${FILE_C:-$FILE_A}

# ---------------------------------------------------------------------------
# FILE_MISSING and SYMBOL_ABSENT: names that must not exist. Asserted, not hoped.
# ---------------------------------------------------------------------------
FILE_MISSING="src/probe_absent_module_qz7.ts"
SYMBOL_ABSENT="probe_absent_symbol_qz7"
PROBE_SELF_DIR="docs/agent-probes"
if [ -e "$REPO/$FILE_MISSING" ]; then
  echo "$FILE_MISSING unexpectedly exists — edit the script and pick another name" >&2
  exit 1
fi
# The kit's own directory is excluded from this check: PROBES.md and this script both name the
# absent symbol, so running the generator against the repository that HOSTS the kit would otherwise
# fail on its own documentation.
if git -C "$REPO" grep -qI "$SYMBOL_ABSENT" -- ":!$PROBE_SELF_DIR" 2>/dev/null; then
  echo "$SYMBOL_ABSENT unexpectedly appears in the repository — pick another name" >&2
  exit 1
fi

# A symbol that DOES exist, so probe E has both halves.
#
# **Declared exactly once, and the longest such name.** The most COMMON symbol would be the wrong
# choice: `fmt`, `main` and `new` are declared in dozens of files, so "is there a function called
# fmt" has no single right answer and the probe stops discriminating between an agent that searched
# and one that guessed.
SYMBOL_PRESENT=$(
  git -C "$REPO" grep -hIE '^[[:space:]]*(export )?(pub )?(async )?(function|fn|def) [A-Za-z_][A-Za-z0-9_]*' \
    -- ":!$PROBE_SELF_DIR" 2>/dev/null |
    sed -E 's/.*(function|fn|def) ([A-Za-z_][A-Za-z0-9_]*).*/\2/' |
    sort | uniq -c |
    awk '$1 == 1 { print length($2), $2 }' |
    sort -rn | awk 'NR==1 { print $2 }'
)
SYMBOL_PRESENT=${SYMBOL_PRESENT:-main}

# A token the repository has FAR more of than a filtered listing will show — probe K needs the true
# count to be out of reach of anything the agent can eyeball.
SYMBOL_COMMON=""
SYMBOL_COMMON_COUNT=0
for candidate in fn function def return import const let class; do
  n=$(git -C "$REPO" grep -oIw "$candidate" -- ":!$PROBE_SELF_DIR" 2>/dev/null | wc -l)
  if [ "$n" -gt "$SYMBOL_COMMON_COUNT" ]; then
    SYMBOL_COMMON=$candidate
    SYMBOL_COMMON_COUNT=$n
  fi
done

# ---------------------------------------------------------------------------
# Needles for probe G. Depth is in tokens, converted at a deliberately
# conservative 4 characters per token — an underestimate of the true depth is
# fine, an overestimate would report a window larger than the real one.
# ---------------------------------------------------------------------------
HEAD_SHORT=$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo nohead)
DEPTHS="8000 32000 64000 128000 200000"

for depth in $DEPTHS; do
  marker="NEEDLE-${HEAD_SHORT}-${depth}"
  target_chars=$((depth * 4))
  file="$OUT/needle-${depth}.txt"
  {
    echo "Filler text follows. Read it all; a marker is hidden inside."
    awk -v total="$target_chars" -v marker="$marker" '
      BEGIN {
        half = total / 2
        written = 0
        n = 0
        placed = 0
        while (written < total) {
          n++
          line = sprintf("Filler line %d: this sentence exists to occupy context and says nothing at all.", n)
          if (!placed && written >= half) {
            print "The marker is: " marker
            placed = 1
          }
          print line
          written += length(line) + 1
        }
        if (!placed) print "The marker is: " marker
      }'
  } >"$file"
  eval "NEEDLE_${depth}=\$marker"
done

# ---------------------------------------------------------------------------
# The key.
# ---------------------------------------------------------------------------
KEY="$OUT/KEY.md"
{
  echo "# Answer key"
  echo
  echo "Generated from \`$REPO\` at commit \`$HEAD_SHORT\`."
  echo "**Do not paste this file into the session under test.**"
  echo
  echo '| Placeholder | Value |'
  echo '|---|---|'
  printf '| `<FILE_A>` | `%s` |\n' "$FILE_A"
  printf '| `<FILE_A_LINES>` | **%s** |\n' "$FILE_A_LINES"
  printf '| `<FILE_A_BYTES>` | %s |\n' "$FILE_A_BYTES"
  printf '| `<FILE_A_SHA256_16>` | `%s` |\n' "$FILE_A_SHA"
  printf '| `<FILE_C>` | `%s` |\n' "$FILE_C"
  printf '| `<FILE_MISSING>` | `%s` (asserted absent) |\n' "$FILE_MISSING"
  printf '| `<LINE_D_NUMBER>` | %s |\n' "$LINE_D_NUMBER"
  printf '| `<SYMBOL_ABSENT>` | `%s` (asserted absent) |\n' "$SYMBOL_ABSENT"
  printf '| `<SYMBOL_PRESENT>` | `%s` |\n' "$SYMBOL_PRESENT"
  printf '| `<SYMBOL_COMMON>` | `%s` |\n' "$SYMBOL_COMMON"
  printf '| `<SYMBOL_COMMON_COUNT>` | **%s** occurrence(s) — probe K compares against this |\n' "$SYMBOL_COMMON_COUNT"
  printf '| `<LANGUAGE>` | whichever you drive the agent in |\n'
  echo
  echo '### `<LINE_D_TEXT>` — byte-identical, this is the comparison'
  echo
  echo '```'
  printf '%s\n' "$LINE_D_TEXT"
  echo '```'
  echo
  echo '### Needles for probe G'
  echo
  echo '| Depth (tokens, approx) | File | Marker |'
  echo '|---|---|---|'
  for depth in $DEPTHS; do
    eval "m=\$NEEDLE_${depth}"
    printf '| %s | `needle-%s.txt` | `%s` |\n' "$depth" "$depth" "$m"
  done
  echo
  echo 'Depth is characters divided by four, which understates the real token count for most'
  echo 'tokenizers. A window measured with these is a floor, not a ceiling.'
} >"$KEY"

echo "key:     $KEY"
echo "needles: $(ls "$OUT"/needle-*.txt | wc -l) file(s) in $OUT"
echo "file_a:  $FILE_A ($FILE_A_LINES lines)"
