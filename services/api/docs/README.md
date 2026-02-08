# Instructivo de Setup: FastAPI + PostgreSQL + Alembic + Docker + pgAdmin

Este documento describe **paso a paso** cómo se configuró el entorno de desarrollo para el proyecto **enterprise-ai-platform**, incluyendo:

* API Gateway con **FastAPI**
* Base de datos **PostgreSQL 15**
* Migraciones con **Alembic**
* Contenedorización con **Docker Compose**
* Administración visual con **pgAdmin**

El objetivo es que cualquier integrante del equipo pueda **replicar el entorno desde cero**.

---

## 1. Requisitos previos

Asegurarse de tener instalado:

* Docker Desktop (con Docker Compose v2)
* Git
* (Opcional) PowerShell / Terminal

No es necesario tener PostgreSQL ni pgAdmin instalados localmente.

---

## 2. Estructura del proyecto

```text
enterprise-ai-platform/
└── services/
    └── api/
        ├── app/
        │   ├── core/
        │   ├── infrastructure/
        │   │   └── db/
        │   │       ├── base.py
        │   │       └── orm/
        │   │           ├── tenant.py
        │   │           ├── role.py
        │   │           ├── user.py
        │   │           ├── conversation.py
        │   │           └── message.py
        │   └── main.py
        ├── alembic/
        │   ├── env.py
        │   └── versions/
        ├── docker-compose.yml
        ├── Dockerfile
        ├── pyproject.toml
        ├── uv.lock
        └── .env.docker
```

---

## 3. Variables de entorno (API en Docker)

Archivo: `services/api/.env.docker`

```env
ENV=dev
API_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

DB_DRIVER=postgresql+psycopg
DB_USER=enterpriseuser
DB_PASSWORD=enterprisepass
DB_HOST=postgres
DB_PORT=5432
DB_NAME=enterpriseaigatewaydev

JWT_SECRET=supersecret
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=120
```

> **Nota:** `DB_HOST=postgres` es el nombre del servicio definido en Docker Compose.

---

## 4. Docker Compose

Archivo: `services/api/docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: enterprise_ai_postgres
    environment:
      POSTGRES_USER: enterpriseuser
      POSTGRES_PASSWORD: enterprisepass
      POSTGRES_DB: enterpriseaigatewaydev
    ports:
      - "55432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U enterpriseuser -d enterpriseaigatewaydev"]
      interval: 5s
      timeout: 5s
      retries: 10

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: enterprise_ai_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@admin.com
      PGADMIN_DEFAULT_PASSWORD: admin
      PGADMIN_CONFIG_SERVER_MODE: "False"
    ports:
      - "5050:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    depends_on:
      postgres:
        condition: service_healthy

  api:
    build:
      context: .
    container_name: enterprise_ai_api
    env_file:
      - .env.docker
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    command: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
  pgadmin_data:
```

---

## 5. Dockerfile de la API

Archivo: `services/api/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock* ./

RUN pip install --no-cache-dir uv
RUN uv sync --frozen

COPY . .

EXPOSE 8000
```

---

## 6. Levantar el entorno completo

Desde el directorio `services/api`:

```bash
docker compose up -d --build
```

Verificar contenedores:

```bash
docker ps
```

Servicios disponibles:

* API: [http://localhost:8000](http://localhost:8000)
* pgAdmin: [http://localhost:5050](http://localhost:5050)

---

## 7. Configurar pgAdmin

Acceder a `http://localhost:5050`

Credenciales:

* Email: `admin@admin.com`
* Password: `admin`

### Registrar servidor

**General**

* Name: `enterprise_ai_postgres`

**Connection**

* Host name/address: `postgres`
* Port: `5432`
* Maintenance database: `enterpriseaigatewaydev`
* Username: `enterpriseuser`
* Password: `enterprisepass`
* Save password: ✔

---

## 8. Alembic – Migraciones

### Crear migración inicial

```bash
docker exec -it enterprise_ai_api uv run alembic revision --autogenerate -m "initial schema"
```

### Aplicar migraciones

```bash
docker exec -it enterprise_ai_api uv run alembic upgrade head
```

### Verificar tablas

```bash
docker exec -it enterprise_ai_postgres psql -U enterpriseuser -d enterpriseaigatewaydev -c "\\dt"
```

---

## 9. Resultado esperado

* Contenedores levantados:

  * `enterprise_ai_api`
  * `enterprise_ai_postgres`
  * `enterprise_ai_pgadmin`
* Base de datos creada
* Tablas generadas por Alembic
* Acceso visual por pgAdmin

---

## 10. Buenas prácticas

* Ejecutar Alembic **siempre dentro del contenedor API**
* No usar `localhost` entre contenedores
* Mantener `.env` (host) y `.env.docker` separados
* Usar `postgresql+psycopg` (psycopg v3)

---

## 11. Próximos pasos sugeridos

* Documentar flujos de autenticación (Auth/JWT)
* Agregar backups automáticos de Postgres
* Definir perfiles `dev / staging / prod`
* Integrar CI con migraciones automáticas

---

**Estado:** ✅ Infraestructura base funcional y documentada
