#!/bin/sh
set -eu

PYTHON="${PYTHON:-python3.11}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python 3.11 is required."
    echo "Install it with: pkg install -y python311 py311-pip"
    exit 1
fi

"$PYTHON" -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
musicclean init

echo
echo "MusicClean is installed in $(pwd)/.venv"
echo "Activate it later with: . .venv/bin/activate"
