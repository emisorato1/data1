# Dockerfile para RAG Generation Service

FROM python:3.12-slim

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias primero (para cache de Docker)
COPY pyproject.toml .
COPY README.md .

# Copiar código fuente
COPY src/ ./src/

# Instalar dependencias con uv
RUN uv pip install --system --no-cache-dir -e .

# Puerto del servidor
EXPOSE 2024

# Variables de entorno por defecto
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Servidor custom con persistencia PostgreSQL (AsyncPostgresSaver + AsyncPostgresStore)
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "2024"]
