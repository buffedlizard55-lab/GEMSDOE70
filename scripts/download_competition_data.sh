#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Owner mirror restoration, NOT an authenticated DrivenData download.
.venv/bin/python scripts/restore_data.py
