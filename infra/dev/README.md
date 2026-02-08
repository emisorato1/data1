# Enterprise AI Platform - Development Environment

Entorno de desarrollo local para la plataforma Enterprise AI con sistema RAG multi-agente.

## 📋 Arquitectura de Servicios

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                          │
│                        http://localhost:3000                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                          │
│                        http://localhost:8000                        │
│  • Autenticación JWT                                                │
│  • Gestión de mensajes                                              │
│  • Proxy al servicio RAG                                            │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENTIC RAG (LangGraph)                          │
│                        http://localhost:2024                        │
│  • Orchestrator (clasificación de consultas)                        │
│  • Public Agent (info pública - cocina)                             │
│  • Private Agent (info privada - técnica)                           │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   POSTGRESQL + PGVECTOR                             │
│                        localhost:5432                               │
│  • Platform DB (usuarios, mensajes)                                 │
│  • Vector DB (documentos, embeddings)                               │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Plan de Operaciones

### Paso 1: Configuración Inicial

```bash
# 1. Ir al directorio de desarrollo
cd infra/dev

# 2. Copiar y configurar variables de entorno
cp .env.example .env

# 3. Editar .env y configurar tu OPENAI_API_KEY
# IMPORTANTE: Necesitas una API key válida de OpenAI
nano .env  # o usa tu editor preferido
```

### Paso 2: Levantar los Servicios

```bash
# Levantar todos los servicios
docker-compose up -d

# Ver logs en tiempo real (opcional)
docker-compose logs -f

# Verificar que todos los servicios estén corriendo
docker-compose ps
```

**Servicios esperados:**
| Servicio | Puerto | Estado esperado |
|----------|--------|-----------------|
| eai-postgres | 5432 | healthy |
| eai-api-gateway | 8000 | healthy |
| eai-agentic-rag | 2024 | healthy |
| eai-frontend | 3000 | running |

### Paso 3: Crear Usuarios de Prueba

```bash
# Instalar dependencias del script
pip install psycopg2-binary argon2-cffi

# Ejecutar script de creación de usuarios
python scripts/create_test_users.py
```

**Usuarios creados:**
| Email | Password | Rol | Acceso |
|-------|----------|-----|--------|
| public@demo.local | password123 | public | Solo info pública (cocina) |
| private@demo.local | password123 | private | Toda la información |
| admin@demo.local | password123 | admin | Administrador |

### Paso 4: Cargar Datos de Prueba

```bash
# Instalar dependencias adicionales
pip install openai python-dotenv

# Ejecutar script de seed de datos
python scripts/seed_test_data.py
```

**Documentos cargados:**
- **3 documentos PÚBLICOS**: Recetas, técnicas de cocina, historia del chocolate
- **3 documentos PRIVADOS**: Mantenimiento de motores, POO, circuitos eléctricos

### Paso 5: Verificar Conectividad

```bash
# 1. Verificar API Gateway
curl http://localhost:8000/api/v1/health

# 2. Verificar Agentic RAG
curl http://localhost:2024/info

# 3. Verificar Frontend
curl http://localhost:3000

# 4. Verificar PostgreSQL
docker exec eai-postgres psql -U eai_user -d eai_platform -c "SELECT count(*) FROM documents;"
```

### Paso 6: Probar la Aplicación

1. **Abrir el navegador**: http://localhost:3000

2. **Login como usuario PÚBLICO** (`public@demo.local` / `password123`):
   - ✅ Preguntar: "¿Cómo se hace la paella valenciana?"
   - ✅ Preguntar: "¿Cuáles son las técnicas de corte en cocina?"
   - ❌ Preguntar: "¿Cómo funciona un motor diesel?" → No debe tener acceso

3. **Login como usuario PRIVADO** (`private@demo.local` / `password123`):
   - ✅ Preguntar: "¿Cómo se hace la paella valenciana?"
   - ✅ Preguntar: "¿Cómo funciona un motor diesel?"
   - ✅ Preguntar: "Explícame la programación orientada a objetos"

4. **Verificar comportamiento sin información**:
   - Preguntar algo que no esté en la base de datos
   - El agente debe responder que no tiene información disponible

## 🧪 Casos de Prueba

### Test 1: Acceso Público
```
Usuario: public@demo.local
Consulta: "¿Qué es la paella valenciana?"
Esperado: Respuesta con información de la receta + cita al documento
```

### Test 2: Restricción de Acceso Público
```
Usuario: public@demo.local
Consulta: "¿Cómo hago mantenimiento a un motor diesel?"
Esperado: "No se encontró información relacionada..."
```

### Test 3: Acceso Privado Completo
```
Usuario: private@demo.local
Consulta: "¿Qué es la programación orientada a objetos?"
Esperado: Respuesta con explicación de POO + cita al documento
```

### Test 4: Consulta Sin Información
```
Usuario: cualquiera
Consulta: "¿Cuál es la capital de Francia?"
Esperado: "No se encontró información relacionada..."
```

## 🔧 Comandos Útiles

```bash
# Ver logs de un servicio específico
docker-compose logs -f api-gateway
docker-compose logs -f agentic-rag
docker-compose logs -f frontend

# Reiniciar un servicio
docker-compose restart api-gateway

# Reconstruir un servicio después de cambios
docker-compose up -d --build api-gateway

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (reset completo)
docker-compose down -v

# Acceder a la base de datos
docker exec -it eai-postgres psql -U eai_user -d eai_platform

# Ver documentos en la base de datos
docker exec eai-postgres psql -U eai_user -d eai_platform -c "SELECT id, metadata->>'title', metadata->>'description' FROM documents;"
```

## 🐛 Troubleshooting

### Error: "OPENAI_API_KEY no configurada"
```bash
# Verificar que el .env tiene la API key
cat .env | grep OPENAI

# Reiniciar el servicio RAG
docker-compose restart agentic-rag
```

### Error: "Connection refused" al API
```bash
# Verificar que el servicio está corriendo
docker-compose ps

# Ver logs del API
docker-compose logs api-gateway
```

### Error: CORS "405 Method Not Allowed" en OPTIONS
El API Gateway necesita el middleware CORS configurado. Verificar que `main.py` incluye:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Error: "column xxx does not exist" en PostgreSQL
Hay una desincronización entre el esquema SQL y los modelos ORM. Solución:
```bash
# Eliminar el volumen y recrear la base de datos
docker-compose down -v
docker-compose up -d
```

### Error: "502 Bad Gateway" al enviar mensajes
El API Gateway no puede comunicarse con el servicio RAG. Verificar:
```bash
# 1. Verificar que agentic-rag está corriendo
docker-compose ps

# 2. Ver logs del RAG
docker-compose logs agentic-rag --tail=50

# 3. Probar conectividad desde el API Gateway
docker-compose exec api-gateway python -c "import httpx; print(httpx.get('http://agentic-rag:2024/info').text)"
```

### Error: "No se encontró información" para todo
```bash
# Verificar que hay documentos en la base de datos
docker exec eai-postgres psql -U postgres -d enterpriseaigatewaydev -c "SELECT count(*) FROM documents;"

# Si está vacío, ejecutar el seed
python scripts/seed_test_data.py
```

### Error de autenticación
```bash
# Verificar que los usuarios existen
docker exec eai-postgres psql -U postgres -d enterpriseaigatewaydev -c "SELECT email, role_id FROM users;"

# Si no hay usuarios, ejecutar el script
python scripts/create_test_users.py
```

### Frontend no carga
```bash
# Verificar logs del frontend
docker-compose logs frontend

# Reconstruir si hay cambios
docker-compose up -d --build frontend
```

### Error de TypeScript en build del frontend
Si hay errores de tipos con `LangChainMessage`, verificar que:
1. `chatApi.ts` importa el tipo desde `@assistant-ui/react-langgraph`
2. Los mensajes de tipo "system" se filtran antes de enviarlos al backend

## 📁 Estructura de Archivos

```
infra/dev/
├── docker-compose.yaml      # Orquestación de servicios
├── env.example              # Variables de entorno de ejemplo
├── README.md                # Este archivo
├── init-db/
│   └── 01-init-extensions.sql  # Esquema de base de datos
└── scripts/
    ├── create_test_users.py    # Crear usuarios de prueba
    └── seed_test_data.py       # Cargar documentos de prueba
```

## 🔗 URLs de Servicios

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Frontend | http://localhost:3000 | Interfaz de chat |
| API Gateway | http://localhost:8000 | API REST |
| API Docs | http://localhost:8000/docs | Documentación Swagger |
| Agentic RAG | http://localhost:2024 | Servicio LangGraph |
| RAG Docs | http://localhost:2024/docs | Documentación RAG |
| PostgreSQL | localhost:5432 | Base de datos |

## 📝 Notas Técnicas Importantes

### Base de Datos
1. **Driver async**: El API Gateway usa `postgresql+asyncpg` como driver de SQLAlchemy para operaciones asíncronas.
2. **Esquema SQL vs ORM**: El archivo `init-db/01-init-extensions.sql` debe estar sincronizado con los modelos ORM. La tabla `tenants` debe incluir la columna `status`.
3. **DEFAULT_TENANT_ID**: El ID del tenant por defecto es `00000000-0000-0000-0000-000000000001` (debe coincidir entre SQL y `seed.py`).

### Comunicación con el Servicio RAG
1. **LangGraph API**: El servicio RAG usa LangGraph API. El flujo correcto es:
   - `POST /threads` para crear el thread
   - `POST /threads/{thread_id}/runs` para ejecutar el grafo
   - `GET /threads/{thread_id}/runs/{run_id}/join` para esperar el resultado
2. **Thread ID**: Debe ser un UUID válido. Se usa el `session_id` del mensaje como `thread_id`.

### API Gateway
1. **CORS**: Es obligatorio el `CORSMiddleware` para que el frontend pueda comunicarse.
2. **Endpoints de Auth**: Disponibles `/auth/login`, `/auth/register`, `/auth/me`, `/auth/session`.

### General
1. **API Key de OpenAI**: Es obligatoria para que el sistema RAG funcione. Sin ella, las consultas fallarán.
2. **Primera ejecución**: La primera vez que se levanten los servicios, puede tomar varios minutos mientras se descargan las imágenes y se construyen los contenedores.
3. **Persistencia**: Los datos de PostgreSQL se persisten en un volumen Docker (`eai-postgres-data`). Para hacer un reset completo, usa `docker-compose down -v`.
4. **Desarrollo**: Para hacer cambios en el código, reconstruye el servicio correspondiente con `docker-compose up -d --build <servicio>`.
