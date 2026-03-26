FROM python:3.11-slim AS base

WORKDIR /app

# Dependências de sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código
COPY src/ ./src/

# Cria diretório para session do Telegram
RUN mkdir -p /app/sessions

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.main"]

# ── Stage de testes ──
FROM base AS test
COPY tests/ ./tests/
RUN pip install --no-cache-dir pytest pytest-asyncio
CMD ["pytest", "tests/", "-v"]
