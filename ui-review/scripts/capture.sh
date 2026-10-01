#!/usr/bin/env bash
#
# capture.sh (ui-review skill) — one screenshot the reviewer may receive: the image, its annotate legend, and a
# sidecar that records WHERE it came from. review.py refuses an image without the sidecar or
# with a non-localhost source: a cloud stack's screenshot holds real participant PII.
#
#   capture.sh <session> <out-dir> <name> [css-selector]
#
#   capture.sh verify-myapp .ui-review/run1 01-record
#   capture.sh verify-myapp .ui-review/run1 02-dialog '[role=dialog]'
#
# Writes <out-dir>/<name>.png (CLEAN — what the model sees), <name>.annotated.png (labels [N] =
# refs @eN, for humans), <name>.legend.json (labels + boxes, sent as text), <name>.src.json
# {url, viewport, capturedAt}. Needs the tool sandbox DISABLED (else the
# file is silently not written) — check the printed size.
set -euo pipefail
SESSION="${1:?session}"; OUT="${2:?out dir}"; NAME="${3:?name}"; SEL="${4:-}"
AB=(agent-browser --session "$SESSION")
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"            # agent-browser resolves a RELATIVE path against its daemon, not this shell
PNG="$OUT/$NAME.png"

URL=$("${AB[@]}" get url 2>/dev/null | tr -d '\r' | tail -1)
case "$URL" in
  http://localhost*|http://127.0.0.1*|http://*.localhost*|https://*.localhost*|file://*) ;;
  *) echo "✗ refusing to capture $URL — ui-review only reviews local stacks (PII)" >&2; exit 2 ;;
esac

VP=$("${AB[@]}" eval 'JSON.stringify({w:window.innerWidth,h:window.innerHeight,dpr:window.devicePixelRatio})' 2>/dev/null | tr -d '\r' | tail -1)

# The model gets the CLEAN image: numbered overlays hide what they label (a clipped button sits
# under its own box). The legend ([N] -> @eN, role, name, box) travels as TEXT; the annotated copy
# is kept for humans. --json reports data.path, where the image really landed.
"${AB[@]}" screenshot ${SEL:+"$SEL"} "$PNG" --json > "$OUT/.$NAME.clean.json" 2>/dev/null || true
if [ ! -s "$PNG" ]; then
  SAVED=$(python3 -c 'import json,sys;print((json.load(open(sys.argv[1])).get("data") or {}).get("path") or "")' "$OUT/.$NAME.clean.json" 2>/dev/null || true)
  [ -n "$SAVED" ] && [ -s "$SAVED" ] && mv "$SAVED" "$PNG"
fi
ANN="$OUT/$NAME.annotated.png"
"${AB[@]}" screenshot ${SEL:+"$SEL"} "$ANN" --annotate --json > "$OUT/$NAME.legend.json" 2>/dev/null || true
if [ ! -s "$ANN" ]; then
  SAVED=$(python3 -c 'import json,sys;print((json.load(open(sys.argv[1])).get("data") or {}).get("path") or "")' "$OUT/$NAME.legend.json" 2>/dev/null || true)
  [ -n "$SAVED" ] && [ -s "$SAVED" ] && mv "$SAVED" "$ANN"
fi
rm -f "$OUT/.$NAME.clean.json"
[ -s "$PNG" ] || { echo "✗ $PNG not written — is the tool sandbox disabled?" >&2; exit 3; }

printf '{"url":%s,"viewport":%s,"capturedAt":"%s"}\n' \
  "$(printf '%s' "$URL" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')" \
  "${VP:-null}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$OUT/$NAME.src.json"
echo "$PNG $(stat -f%z "$PNG" 2>/dev/null || stat -c%s "$PNG")B $URL"
