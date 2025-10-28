# ==============================
#  STAGE 1: Base Python Image
# ==============================
FROM python:3.11-slim AS builder

# Define a variável de ambiente para evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Campo_Grande

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto para dentro do container
COPY . .

# Atualiza os repositórios e instala as dependências de sistema
# Necessárias para o WeasyPrint, PDF e Streamlit
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
    build-essential \
    wget \
    curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# ==============================
#  STAGE 2: Final runtime image
# ==============================
FROM python:3.11-slim

WORKDIR /app

# Copia os arquivos instalados do builder
COPY --from=builder /usr/local /usr/local
COPY . .

# Expõe a porta padrão do Streamlit
EXPOSE 8501

# Define variáveis de ambiente do Streamlit
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Comando para iniciar o Streamlit
CMD sh -c "streamlit run app.py --server.port=\$PORT --server.address=0.0.0.0"

