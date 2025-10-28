FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=America/Campo_Grande

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    libgirepository-1.0-1 \
    gobject-introspection \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Remove variáveis injetadas incorretamente pelo Railway
ENV STREAMLIT_SERVER_PORT=8501

# ✅ Importante: dá permissão de execução ao entrypoint
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/bin/bash", "/app/docker-entrypoint.sh"]
