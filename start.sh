#!/usr/bin/env bash

set -e

# Move to script directory
cd "$(dirname "$0")"

echo "Loading .env..."

if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found"
    exit 1
fi

# Export environment variables
set -a
. .env
set +a

# Create venv if missing
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    if command -v python >/dev/null 2>&1; then
        python -m venv .venv
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m venv .venv
    elif command -v py >/dev/null 2>&1; then
        py -3 -m venv .venv
    else
        echo "ERROR: Python interpreter not found to create virtual environment"
        exit 1
    fi
fi

# Use venv python directly
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
    LITELLM_CMD=".venv/bin/litellm"
elif [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
    LITELLM_CMD=".venv/Scripts/litellm.exe"
else
    echo "ERROR: Could not locate virtual environment Python interpreter"
    exit 1
fi

# Install LiteLLM if needed
if ! "$PYTHON" -c "import importlib.util; exit(0 if importlib.util.find_spec('litellm') else 1)" >/dev/null 2>&1; then
    echo "Installing LiteLLM..."
    "$PYTHON" -m pip install --upgrade pip
    "$PYTHON" -m pip install "litellm[proxy]"
fi

echo "Starting LiteLLM..."

if [ -x "$LITELLM_CMD" ]; then
    exec "$LITELLM_CMD" --config config.yaml --detailed_debug
else
    exec "$PYTHON" -m litellm.main --config config.yaml --detailed_debug
fi