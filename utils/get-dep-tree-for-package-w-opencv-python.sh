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
# Forcibly install opencv-python 4.10.0.82 to avoid numpy 2 conflict.
uv pip install --quiet --python "$PYTHON_BIN" "numpy==1.26.4" "opencv-python==4.10.0.82"
uv pip install --quiet --python "$PYTHON_BIN" "$PACKAGE"
uv pip tree --python "$PYTHON_BIN" --show-version-specifiers --package "$BASE_PACKAGE"
