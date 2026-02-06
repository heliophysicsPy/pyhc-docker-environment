#!/bin/bash

set -euo pipefail

PACKAGE=$1
BASE_PACKAGE=$(echo "$PACKAGE" | sed 's/\[.*\]//')
BASE_PACKAGE=$(echo "$BASE_PACKAGE" | sed -E 's/[<>=!].*$//')

TEMP_DIR=$(mktemp -d)
cleanup() {
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

VENV_PATH="$TEMP_DIR/.venv"
PYTHON_BIN="$VENV_PATH/bin/python"

uv venv --quiet "$VENV_PATH"
# Force httpcore 1.0.8 to avoid known h11 conflict.
uv pip install --quiet --python "$PYTHON_BIN" "httpcore==1.0.8"
uv pip install --quiet --python "$PYTHON_BIN" "$PACKAGE"
uv pip tree --python "$PYTHON_BIN" --show-version-specifiers --package "$BASE_PACKAGE"
