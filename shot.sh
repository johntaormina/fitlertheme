#!/bin/sh
# Render out/preview.html -> assets/preview.png at 2x.
# ponytail: shells out to Chrome instead of taking a real terminal screenshot.
# A real capture needs a live window and screen-recording permission; this is
# reproducible and runs in CI. Add genuine screenshots to assets/ by hand.
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"

[ -x "$CHROME" ] || { echo "Chrome not found. Set CHROME=/path/to/chrome" >&2; exit 1; }

python3 "$DIR/build.py" >/dev/null
mkdir -p "$DIR/assets"

"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --screenshot="$DIR/assets/preview.png" \
  --window-size=1200,640 \
  --force-device-scale-factor=2 \
  --default-background-color=00000000 \
  "file://$DIR/out/preview.html" 2>/dev/null

echo "assets/preview.png  $(du -h "$DIR/assets/preview.png" | cut -f1)"
