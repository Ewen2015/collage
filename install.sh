#!/usr/bin/env bash
# Install the collage skill's Python dependencies and verify the package.
# Run once, from inside the installed collage/ folder:
#   bash install.sh
set -eu
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
echo "collage: installing Python dependencies with $PY ..."
"$PY" -m pip install -r requirements.txt
echo
echo "collage: verifying the installed skill ..."
"$PY" scripts/check_setup.py
