#!/bin/bash

set -euo pipefail

PACKAGE=$1
BASE_PACKAGE=$(echo "$PACKAGE" | sed 's/\[.*\]//')
BASE_PACKAGE=$(echo "$BASE_PACKAGE" | sed -E 's/[<>=!].*$//')

TEMP_DIR=$(mktemp -d)
cleanup() {
  popd >/dev/null 2>&1 || true
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

pushd "$TEMP_DIR" >/dev/null

uv venv --quiet .venv
# Force httpcore 1.0.8 to avoid known h11 conflict.
uv pip install --quiet --python .venv/bin/python "httpcore==1.0.8"
uv pip install --quiet --python .venv/bin/python "$PACKAGE"
uv pip tree --python .venv/bin/python --show-version-specifiers --package "$BASE_PACKAGE"

popd >/dev/null
