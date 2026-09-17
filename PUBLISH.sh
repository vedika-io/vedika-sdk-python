#!/usr/bin/env bash
# Prepare local distributions. Publishing is a separate release action.
set -euo pipefail
cd "$(dirname "$0")"
output_dir="${1:?Usage: PUBLISH.sh ABSOLUTE_OUTPUT_DIRECTORY}"
[[ "$output_dir" = /* ]] || { echo 'Output directory must be absolute.' >&2; exit 2; }
mkdir -p "$output_dir"
python_bin="${PYTHON:-python3}"
"$python_bin" -m pytest tests
"$python_bin" -m build --no-isolation --outdir "$output_dir"
