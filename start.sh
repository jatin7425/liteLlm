#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# ---------------------------------------------------------------------------
# Local dev only. On Render, env vars are injected directly and no .env exists.
# `set -a` auto-exports everything sourced, which handles quoted values and
# spaces correctly (unlike a manual export loop).
# ---------------------------------------------------------------------------
if [ -d ".venv" ]; then
    echo "Activating virtualenv..."
    # shellcheck disable=SC1091
    . .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate 2>/dev/null || true
fi

if [ -f ".env" ]; then
    echo "Loading .env..."
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
else
    echo "No .env found - using injected environment variables."
fi

# ---------------------------------------------------------------------------
# Render assigns $PORT and health-checks it. Binding anywhere else fails deploy.
# ---------------------------------------------------------------------------
PORT="${PORT:-4000}"

# ---------------------------------------------------------------------------
# --detailed_debug logs full request/response bodies including credentials.
# Off unless explicitly enabled.
# ---------------------------------------------------------------------------
DEBUG_FLAG=""
if [ "${LITELLM_DEBUG:-false}" = "true" ]; then
    echo "WARNING: detailed debug enabled - logs will contain request bodies."
    DEBUG_FLAG="--detailed_debug"
fi

# ---------------------------------------------------------------------------
# Fail fast on missing config rather than letting litellm start with no routes.
# ---------------------------------------------------------------------------
if [ ! -f "config.yaml" ]; then
    echo "ERROR: config.yaml not found in $(pwd)" >&2
    exit 1
fi

if [ -z "${LITELLM_MASTER_KEY:-}" ]; then
    echo "WARNING: LITELLM_MASTER_KEY is not set - proxy will be unauthenticated." >&2
fi

echo "Starting LiteLLM on port ${PORT}..."

if command -v litellm >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    exec litellm --config config.yaml --host 0.0.0.0 --port "${PORT}" ${DEBUG_FLAG}
fi

if command -v python3 >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    exec python3 -m litellm --config config.yaml --host 0.0.0.0 --port "${PORT}" ${DEBUG_FLAG}
fi

echo "ERROR: litellm is not installed. Check requirements.txt and the Docker build." >&2
exit 1
