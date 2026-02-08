#!/bin/sh
set -e

# Ejecutar migraciones
echo "Running database migrations..."
alembic upgrade head

# Iniciar la aplicación
echo "Starting application..."
exec "$@"
