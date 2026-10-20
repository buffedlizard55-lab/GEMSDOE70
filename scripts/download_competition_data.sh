#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Reconstruct SHA-256 pinned core & public external layers from public mirrors (0 REST API calls).
PY="${PYTHON:-.venv/bin/python}"
if [ ! -x "$PY" ]; then
  PY="python3"
fi
"$PY" scripts/restore_data.py
"$PY" scripts/fetch_data.py
