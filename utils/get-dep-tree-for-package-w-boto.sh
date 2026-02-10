#!/bin/bash

set -euo pipefail

PACKAGE=$1
BASE_PACKAGE=$(echo "$PACKAGE" | sed 's/\[.*\]//')
BASE_PACKAGE=$(echo "$BASE_PACKAGE" | sed -E 's/[<>=!].*$//')
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

TEMP_DIR=$(mktemp -d)
cleanup() {
  popd >/dev/null 2>&1 || true
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

pushd "$TEMP_DIR" >/dev/null

uv venv --quiet .venv

# Prefer boto pins from current compile output when available, then fall back to
# repo lockfile. This keeps per-package extraction aligned with current solver choices.
LOCKFILE_PRIMARY="/tmp/new-resolved-versions.txt"
LOCKFILE_FALLBACK="$SCRIPT_DIR/../docker/pyhc-environment/contents/resolved-versions.txt"

extract_pin() {
  local pkg="$1"
  local file="$2"
  if [[ -f "$file" ]]; then
    grep -E "^${pkg}==" "$file" | head -n 1 | cut -d '=' -f 3
  fi
}

BOTO3_VERSION="$(extract_pin "boto3" "$LOCKFILE_PRIMARY")"
BOTOCORE_VERSION="$(extract_pin "botocore" "$LOCKFILE_PRIMARY")"

if [[ -z "$BOTO3_VERSION" || -z "$BOTOCORE_VERSION" ]]; then
  BOTO3_VERSION="${BOTO3_VERSION:-$(extract_pin "boto3" "$LOCKFILE_FALLBACK")}"
  BOTOCORE_VERSION="${BOTOCORE_VERSION:-$(extract_pin "botocore" "$LOCKFILE_FALLBACK")}"
fi

if [[ -z "$BOTO3_VERSION" || -z "$BOTOCORE_VERSION" ]]; then
  echo "ERROR: Failed to determine boto3/botocore pins for extraction." >&2
  echo "Looked in: $LOCKFILE_PRIMARY and $LOCKFILE_FALLBACK" >&2
  exit 1
fi

echo "Using boto pins for extraction: boto3==$BOTO3_VERSION botocore==$BOTOCORE_VERSION" >&2
uv pip install --quiet --python .venv/bin/python "boto3==$BOTO3_VERSION" "botocore==$BOTOCORE_VERSION"
uv pip install --quiet --python .venv/bin/python "$PACKAGE"
uv pip tree --python .venv/bin/python --show-version-specifiers --package "$BASE_PACKAGE"

popd >/dev/null
