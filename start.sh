#!/bin/bash
# Launcher script that uses the virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/test_env/bin/python"

exec "$VENV_PYTHON" "$SCRIPT_DIR/run_amarelo.py" "$@"