#!/usr/bin/env bash
set -e

# Força modo headless
export STREAMLIT_HEADLESS=true

# Lê a porta definida pelo Railway ou usa 8501 localmente
PORT_RAW="${PORT:-8501}"

# Verifica se é numérica
if ! [[ "$PORT_RAW" =~ ^[0-9]+$ ]]; then
  PORT_RAW="8501"
fi

echo "[entrypoint] Starting Streamlit on port $PORT_RAW"

# Se a Railway injetar literalmente '$PORT', substituímos por 8501
if [ "${STREAMLIT_SERVER_PORT}" = '$PORT' ]; then
  export STREAMLIT_SERVER_PORT="8501"
else
  unset STREAMLIT_SERVER_PORT || true
fi
unset STREAMLIT_SERVER_ADDRESS || true

export PORT="$PORT_RAW"
export STREAMLIT_SERVER_PORT="$PORT_RAW"

exec streamlit run app.py --server.port "$PORT_RAW" --server.address 0.0.0.0
