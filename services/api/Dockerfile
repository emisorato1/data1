FROM python:3.13-slim

WORKDIR /app

ENV UV_NO_VENV=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# deps sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# instalar uv
RUN pip install --no-cache-dir uv

# copiar dependencias primero (cache)
COPY pyproject.toml ./

# instalar deps SIN virtualenv
RUN uv pip install --system .

# copiar código y migraciones
COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

# Script de entrada para migraciones automáticas
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
