#!/usr/bin/env bash
# Fetch 4 chapters of the light-dark series from examist.jp
# and convert HTML -> Markdown so any translator can consume them.
#
# Requirements:
#   brew install pandoc
#   (curl is already on macOS)
#
# Usage:
#   ./fetch.sh          # downloads *.html and converts to *.md
#   ./fetch.sh clean    # remove generated files

set -euo pipefail

BASE="https://examist.jp/light-dark"
CHAPTERS=(1 2 3 4 5 6 7 8)
OUT_DIR="$(dirname "$0")/raw"

if [[ "${1:-}" == "clean" ]]; then
  rm -rf "$OUT_DIR"
  echo "cleaned"
  exit 0
fi

mkdir -p "$OUT_DIR"

for n in "${CHAPTERS[@]}"; do
  url="${BASE}/light-dark${n}/"
  html="${OUT_DIR}/chapter-${n}.html"
  md="${OUT_DIR}/chapter-${n}.md"

  echo "==> fetching ${url}"
  curl -sSL \
    -H "User-Agent: Mozilla/5.0" \
    -o "$html" \
    "$url"

  echo "==> converting to markdown"
  # --from html      : input is HTML
  # --to gfm         : GitHub-Flavoured Markdown (keeps tables + images)
  # --wrap=none      : do not hard-wrap lines (better for translators)
  # --extract-media  : pull inline images to a folder if you want them local
  pandoc \
    --from html \
    --to gfm \
    --wrap=none \
    "$html" -o "$md"

  echo "    -> ${md}"
done

echo
echo "Done. Files are in: ${OUT_DIR}"
