#!/usr/bin/env bash
#
# Renders each page of media/architecture/architecture.drawio to BOTH an SVG
# and a PNG. Page names (e.g. "high_level/tier_1") are used verbatim as the
# output path under media/architecture/ — this is how the drawio source and
# the committed images are kept from diverging.
#
# - SVG (dark theme, transparent, Outfit font embedded): used by the docs site,
#   which renders SVG natively and stays sharp at any zoom level.
# - PNG (default theme, scale 2, branded background baked in): used by the
#   READMEs shown on GitHub and PyPI/npm. Those surfaces fetch images via
#   raw.githubusercontent.com, which serves .svg as text/plain — so an <img>
#   pointing at a raw SVG renders broken. PNG is served as image/png and works.
#
# Run manually after editing the .drawio file:
#   pnpm run docs:render-diagrams
#
# Requires: docker, curl. The Outfit font is NOT committed — it is downloaded
# on demand (and checksum-verified) into a gitignored cache below.

set -euo pipefail

DOCS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCH_DIR="${DOCS_DIR}/media/architecture"
FONTS_DIR="${DOCS_DIR}/fonts"
DRAWIO_FILE="${ARCH_DIR}/architecture.drawio"
IMAGE="rlespinasse/drawio-export:latest"

# Outfit variable font (OFL-1.1), pinned to a specific google/fonts commit via the
# jsDelivr CDN and verified by SHA-256. Pinning the commit + checksum makes renders
# reproducible without committing the 110 KB binary to the repo. Bump both together
# to upgrade. License: docs/fonts/Outfit/OFL.txt.
FONT_FILE="${FONTS_DIR}/Outfit/Outfit-VariableFont_wght.ttf"
FONT_URL="https://cdn.jsdelivr.net/gh/google/fonts@5f246070882b903ed95a911dba83d9d4a6836152/ofl/outfit/Outfit%5Bwght%5D.ttf"
FONT_SHA256="fc7287273e66929776e2ba54f144fe699080bec29f61bf649d70d871468aeade"

if [ ! -f "${DRAWIO_FILE}" ]; then
  echo "❌ Source file not found: ${DRAWIO_FILE}" >&2
  exit 1
fi

for cmd in docker curl python3 sha256sum; do
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "❌ ${cmd} is required but not on PATH." >&2
    exit 1
  fi
done

# Download + verify the font if it is missing or its checksum does not match.
if [ ! -f "${FONT_FILE}" ] || [ "$(sha256sum "${FONT_FILE}" | awk '{print $1}')" != "${FONT_SHA256}" ]; then
  echo "⬇️  Fetching Outfit font (not committed; checksum-pinned)..."
  mkdir -p "$(dirname "${FONT_FILE}")"
  curl -fsSL "${FONT_URL}" -o "${FONT_FILE}"
  ACTUAL_SHA="$(sha256sum "${FONT_FILE}" | awk '{print $1}')"
  if [ "${ACTUAL_SHA}" != "${FONT_SHA256}" ]; then
    echo "❌ Font checksum mismatch: expected ${FONT_SHA256}, got ${ACTUAL_SHA}" >&2
    rm -f "${FONT_FILE}"
    exit 1
  fi
fi

mapfile -t PAGES < <(grep -oE '<diagram name="[^"]*"' "${DRAWIO_FILE}" \
  | sed -E 's/^<diagram name="([^"]*)"$/\1/')

if [ "${#PAGES[@]}" -eq 0 ]; then
  echo "❌ No <diagram> pages found in ${DRAWIO_FILE}" >&2
  exit 1
fi

echo "🔄 Pulling ${IMAGE}..."
docker pull -q "${IMAGE}" >/dev/null

echo "🎨 Rendering ${#PAGES[@]} pages from architecture.drawio..."
LOG_FILTER='dbus|CONSOLE|sandbox_linux|gbm_support|viz/service|bluetooth|Floss manager|gpu/ipc'
for i in "${!PAGES[@]}"; do
  PAGE="${PAGES[$i]}"
  OUTPUT_SVG="${ARCH_DIR}/${PAGE}.svg"
  OUTPUT_PNG="${ARCH_DIR}/${PAGE}.png"
  PAGE_INDEX=$((i + 1))  # drawio CLI is 1-based
  mkdir -p "$(dirname "${OUTPUT_SVG}")"
  rm -f "${OUTPUT_SVG}" "${OUTPUT_PNG}"
  echo "  [${PAGE_INDEX}] ${PAGE} → media/architecture/${PAGE}.{svg,png}"
  docker run --rm \
    --user "$(id -u):$(id -g)" \
    --entrypoint /bin/sh \
    --shm-size=2g \
    -e HOME=/tmp \
    -e XDG_DATA_HOME=/tmp/.local/share \
    -v "${ARCH_DIR}:/data" \
    -v "${FONTS_DIR}:/fonts:ro" \
    "${IMAGE}" \
    -c "mkdir -p /tmp/.local/share/fonts && cp -r /fonts/* /tmp/.local/share/fonts/ && fc-cache -f /tmp/.local/share/fonts >/dev/null && xvfb-run -a drawio --export --format svg --svg-theme dark --page-index ${PAGE_INDEX} --output '/data/${PAGE}.svg' --no-sandbox /data/architecture.drawio && xvfb-run -a drawio --export --format png --scale 2 --page-index ${PAGE_INDEX} --output '/data/${PAGE}.png' --no-sandbox /data/architecture.drawio" \
    2>&1 | grep -vE "${LOG_FILTER}" || true
  if [ ! -s "${OUTPUT_SVG}" ] || [ ! -s "${OUTPUT_PNG}" ]; then
    echo "❌ Failed to render page ${PAGE_INDEX} '${PAGE}' — SVG or PNG missing." >&2
    exit 1
  fi
done

echo "🔤 Embedding Outfit font into SVGs..."
FONT_FILE="${FONT_FILE}" ARCH_DIR="${ARCH_DIR}" python3 <<'PY'
import base64
import os
import pathlib

font_path = pathlib.Path(os.environ["FONT_FILE"])
arch_dir = pathlib.Path(os.environ["ARCH_DIR"])

font_b64 = base64.b64encode(font_path.read_bytes()).decode()
style = (
    "<style>"
    "@font-face{"
    "font-family:'Outfit';"
    "font-style:normal;"
    "font-weight:100 900;"
    f"src:url(data:font/ttf;base64,{font_b64}) format('truetype');"
    "}"
    "</style>"
)

for svg_path in sorted(arch_dir.rglob("*.svg")):
    content = svg_path.read_text()
    if "@font-face" in content:
        continue
    if "<defs>" not in content:
        raise SystemExit(f"❌ No <defs> tag in {svg_path}; cannot inject @font-face")
    svg_path.write_text(content.replace("<defs>", f"<defs>{style}", 1))
    print(f"  {svg_path.relative_to(arch_dir)}")
PY

echo "✅ Done. Rendered ${#PAGES[@]} pages (SVG + PNG)."
