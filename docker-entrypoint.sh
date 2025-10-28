#!/usr/bin/env bash
set -e

# Remove conflicting port overrides injected by hosting providers
unset STREAMLIT_SERVER_ADDRESS || true

# Default to port 8501 when $PORT é ausente
PORT="${PORT:-8501}"
export STREAMLIT_SERVER_PORT="$PORT"

exec streamlit run app.py --server.port "$PORT" --server.address 0.0.0.0
