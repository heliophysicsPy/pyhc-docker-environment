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
uv pip install --quiet --python .venv/bin/python "$PACKAGE"
uv pip tree --python .venv/bin/python --show-version-specifiers --package "$BASE_PACKAGE"

popd >/dev/null
