#!/usr/bin/env bash

set -e

# Move to script directory
cd "$(dirname "$0")"

# Activate virtual environment if present
if [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    . .venv/Scripts/activate 2>/dev/null || . .venv/bin/activate 2>/dev/null || true
fi

if [ -f ".env" ]; then
    echo "Loading .env..."
    while IFS= read -r line || [ -n "$line" ]; do
        line=$(printf '%s\n' "$line" | tr -d '\r')
        case "$line" in
            ""|"#"*) continue ;;
            *) export "$line" ;;
        esac
    done < ".env"
else
    echo "No .env file found; using environment variables from Render if available"
fi

echo "Starting LiteLLM..."

if command -v litellm >/dev/null 2>&1; then
    exec litellm --config config.yaml --detailed_debug
fi

if command -v python >/dev/null 2>&1 && python -c "import importlib.util; exit(0 if importlib.util.find_spec('litellm') else 1)" >/dev/null 2>&1; then
    exec python -m litellm.main --config config.yaml --detailed_debug
fi

if command -v python3 >/dev/null 2>&1 && python3 -c "import importlib.util; exit(0 if importlib.util.find_spec('litellm') else 1)" >/dev/null 2>&1; then
    exec python3 -m litellm.main --config config.yaml --detailed_debug
fi

echo "ERROR: LiteLLM is not installed. Make sure Render installs dependencies from requirements.txt."
exit 1


if [ -x "$LITELLM_CMD" ]; then
    exec "$LITELLM_CMD" --config config.yaml --detailed_debug
else
    exec "$PYTHON" -m litellm.main --config config.yaml --detailed_debug
fi