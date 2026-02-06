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
# Force boto3/botocore to avoid known botocore conflict during tree extraction.
uv pip install --quiet --python "$PYTHON_BIN" "boto3==1.40.46" "botocore==1.40.46"
uv pip install --quiet --python "$PYTHON_BIN" "$PACKAGE"
uv pip tree --python "$PYTHON_BIN" --show-version-specifiers --package "$BASE_PACKAGE"
