
# Dockerfile
FROM python:3.11-slim-bookworm

# Ambiente e runtime do Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app

# Dependências de sistema mínimas:
# - libmagic1: usado por 'unstructured' e detecção de tipos de arquivo
# - file: utilitário que usa libmagic (opcional mas útil para debug)
# - curl: para healthcheck (opcional)
# - ca-certificates: HTTPS confiável
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
      libmagic1 \
      file \
      curl \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia o código da aplicação
# Se o seu main.py estiver na raiz (recomendado):
COPY main.py ./
COPY ./app ./app

# Cria diretórios de runtime (persistidos no volume no docker-compose)
RUN mkdir -p /data/uploads /data/chroma_db && \
    adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /data /app

# Usuário não-root
USER appuser

# Facilita imports 'app.*'
ENV PYTHONPATH=/app

# Porta do servidor
EXPOSE 8000

# Comando padrão (combina com 'main.py' na raiz)
# Se seu main.py está dentro de app/, troque para: "app.main:app"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--timeout-keep-alive", "120"]

# (Opcional) Healthcheck dentro do container (requer curl)
# HEALTHCHECK --interval=30s --timeout=5s --retries=5 --start-period=20s \
#   CMD curl -sf http://localhost:8000/health || exit 1
