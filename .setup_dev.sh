#!/usr/bin/env bash
# Install into an explicitly activated environment; preserve other environments.
set -euo pipefail
cd "$(dirname "$0")"
python - <<'PY'
import os
import sys
if sys.version_info < (3, 11):
    raise SystemExit("PeriScope requires Python 3.11+; create and activate a new environment.")
if sys.prefix == sys.base_prefix and not os.environ.get("CONDA_PREFIX"):
    raise SystemExit("Activate a virtual or conda environment before running this script.")
PY
python -m pip install -e '.[dev,docs]'
pre-commit install
