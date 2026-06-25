#!/usr/bin/env bash
# scripts/update_public_wheel.sh
# to run make executable in terminal first by running `chmod +x scripts/update_public_wheel.sh` (assumes you put the shell script update_public_wheel.sh in scripts/ folder on root)
#
# Local-dev equivalent of what app.yml does in CI.
# Run this after `uv build` to:
#   1. Remove the old wheel from public/
#   2. Copy the new wheel to public/
#   3. Patch the version string in app/js/pyodide-worker.js
#
# Usage (from repo root):
#   uv build && bash scripts/update_public_wheel.sh
#
# After running, check the diff then commit:
#   git diff app/js/pyodide-worker.js public/
#   git add public/ app/js/pyodide-worker.js
#   git commit -m "chore: update public wheel to $(ls public/drumscript-*.whl | xargs basename)"

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# ------------------------------------------------------------------
# 1. Find the newly-built wheel in dist/
# ------------------------------------------------------------------
WHL_PATH=$(ls dist/drumscript-*-py3-none-any.whl 2>/dev/null | sort -V | tail -1 || true)

if [[ -z "${WHL_PATH}" ]]; then
    echo "Error: no wheel found in dist/. Run 'uv build' first." >&2
    exit 1
fi

WHL_FILE=$(basename "${WHL_PATH}")
echo "Found wheel: ${WHL_FILE}"

# ------------------------------------------------------------------
# 2. Remove old wheels from public/  (keep other files untouched)
# ------------------------------------------------------------------
for OLD in public/drumscript-*-py3-none-any.whl; do
    # The glob expands to the literal string if no matches, so guard:
    [[ -f "${OLD}" ]] || continue
    if [[ "$(basename "${OLD}")" != "${WHL_FILE}" ]]; then
        echo "Removing old wheel: ${OLD}"
        git rm --cached "${OLD}" 2>/dev/null || true
        rm -f "${OLD}"
    fi
done

# ------------------------------------------------------------------
# 3. Copy new wheel to public/
# ------------------------------------------------------------------
if [[ ! -f "public/${WHL_FILE}" ]]; then
    cp "${WHL_PATH}" public/
    echo "Copied → public/${WHL_FILE}"
else
    echo "public/${WHL_FILE} already present, skipping copy"
fi

# ------------------------------------------------------------------
# 4. Patch the version in pyodide-worker.js
#    (same sed pattern as app.yml uses at deploy time)
# ------------------------------------------------------------------
WORKER="app/js/pyodide-worker.js"
if [[ -f "${WORKER}" ]]; then
    # -i '' for macOS BSD sed; -i for GNU sed — try both
    if sed --version 2>&1 | grep -q GNU; then
        sed -i "s|drumscript-[0-9][0-9.]*-py3-none-any\.whl|${WHL_FILE}|g" "${WORKER}"
    else
        sed -i '' "s|drumscript-[0-9][0-9.]*-py3-none-any\.whl|${WHL_FILE}|g" "${WORKER}"
    fi
    echo "Patched ${WORKER}"
    grep "whl" "${WORKER}"
else
    echo "Warning: ${WORKER} not found — skipping worker patch"
fi

# ------------------------------------------------------------------
echo ""
echo "Done. Next steps:"
echo "  git diff ${WORKER} public/"
echo "  git add public/ ${WORKER}"
echo "  git commit -m 'chore: update public wheel to ${WHL_FILE}'"
