#!/usr/bin/env bash
# Install the collage-art skill's Python dependencies and verify the package.
# Run once, from inside the installed collage-art/ folder:
#   bash install.sh
set -eu
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
echo "collage-art: installing Python dependencies with $PY ..."
"$PY" -m pip install -r requirements.txt
echo
echo "collage-art: verifying the installed skill ..."
"$PY" scripts/check_setup.py
