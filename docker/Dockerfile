# ==============================================================================
# Stage 1: BUILDER
# Instala dependencias en un entorno con compiladores.
# El resultado NO se incluye en la imagen final.
# ==============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Dependencias de compilacion para psycopg2, numpy, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv para gestionar dependencias (mismo gestor que el proyecto)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiar solo archivos de dependencias para aprovechar cache de capas Docker
COPY pyproject.toml uv.lock ./

# Exportar requirements y luego instalar en /install para copiar limpio al runtime
RUN uv export --no-dev --no-editable --frozen --no-emit-project -o requirements.txt \
    && pip install \
        --no-cache-dir \
        --no-compile \
        --prefix=/install \
        -r requirements.txt

# Limpiar artefactos innecesarios de las dependencias instaladas
RUN find /install -type d -name "tests" -exec rm -rf {} + 2>/dev/null; \
    find /install -type d -name "test" -exec rm -rf {} + 2>/dev/null; \
    find /install -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; \
    find /install -name "*.pyc" -delete 2>/dev/null; \
    find /install -name "*.pyo" -delete 2>/dev/null; \
    find /install -name "*.dist-info" -type d -exec sh -c 'rm -f "$1"/RECORD "$1"/LICENSE* "$1"/NOTICE*' _ {} \; 2>/dev/null; \
    rm -rf /install/lib/python3.12/site-packages/pip 2>/dev/null; \
    true

# ==============================================================================
# Stage 2: RUNTIME
# Imagen minima con solo lo necesario para ejecutar.
# ==============================================================================
FROM python:3.12-slim AS runtime

# --- Seguridad: usuario no-root (UID 1000 = convencion GKE) ---
RUN groupadd -r -g 1000 appuser && \
    useradd -r -g appuser -u 1000 -d /app -s /sbin/nologin -c "App User" appuser

WORKDIR /app

# Dependencias de runtime (libpq para PostgreSQL, curl para healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove

# Copiar dependencias Python del builder
COPY --from=builder /install /usr/local

# Copiar codigo fuente con ownership correcto
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini .

# --- Variables de entorno ---
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# --- Health check ---
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Cambiar a usuario no-root DESPUES de copiar archivos
USER appuser

EXPOSE 8000

# Copiar entrypoint
COPY --chown=appuser:appuser docker/entrypoint.sh .
RUN chmod +x entrypoint.sh

# Usar entrypoint para migraciones + uvicorn (exec form para senales correctas)
ENTRYPOINT ["./entrypoint.sh"]
