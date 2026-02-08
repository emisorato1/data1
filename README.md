# enterprise-ai-platform


```

```
## Levantar toda la infra

Mirar el readme en la parte de infra y seguir los pasos


## indexacion

## Requisitos previos


### CONECTARSE A LA VPN con la maquina


### Instalación de drivers ODBC

#### Linux (Ubuntu/Debian)

```bash
# Instalar unixODBC
sudo apt-get install unixodbc unixodbc-dev

# Agregar repositorio de Microsoft
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo add-apt-repository "$(curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list)"

# Instalar driver ODBC para SQL Server
sudo apt-get update
sudo apt-get install msodbcsql18
```

Verificar que los drivers están instalados:
```bash
odbcinst -q -d
```

Debería mostrar:
```
[ODBC Driver 18 for SQL Server]
```

#### Windows

1. Descargar el instalador desde: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

2. Ejecutar el instalador `msodbcsql.msi` y seguir los pasos

3. Verificar la instalación abriendo PowerShell:
```powershell
Get-OdbcDriver | Where-Object {$_.Name -like "*SQL Server*"}
```

O desde el Panel de Control:
- Buscar "ODBC Data Sources" 
- En la pestaña "Drivers" debe aparecer "ODBC Driver 18 for SQL Server"





### - 1° metadata

Posicionarse en metadata-pipeline:

```bash
cd services/rag-indexation/metadata-pipelines
```
Crear el entorno y sincronizar:
```bash
uv sync
```

Activar el entorno virtual:
```bash
source .venv/bin/activate

venv .\.venv\Scripts\activate.ps1

.\.venv\Scripts\activate
```

Ejecutar el pipeline:
```bash
uv run python -m src.main
```

Desactiva el entorno virtual

### - 2° pipeline pdf

Posicionarse en pipeline-pdfs:

```bash
cd services/rag-indexation/data-pipelines/index-base/pipeline-pdfs
```
Crear el entorno y sincronizar:
```bash
uv sync
```
Activar el entorno virtual:
```bash
source .venv/bin/activate

venv .\.venv\Scripts\activate.ps1
```

Ejecutar el pipeline:
```bash
python pipeline_main.py "copy-path"

python pipeline_main.py "copy-path"--save
```


## Pruebas:

Abrir el chat desde http://localhost:3000/ (solo se van a poder hacer consultas como usuario privado)



### - curl para preguntar info privada siendo usuario PUBLICO

```bash
curl -X POST http://localhost:8000/api/v1/messages/run \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_role": "public",
    "content": "decime la Estructura y Metadatos del Proyecto?"
  }' | jq '.assistant_message.sources[] | {nombre: .source_name, score: .score, snippet: .snippet}'
```

### - curl para preguntar info publica siendo usuario PUBLICO

```bash
curl -X POST http://localhost:8000/api/v1/messages/run \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_role": "public",
    "content": "decime como hacer tacos?"
  }' | jq '.assistant_message.sources[] | {nombre: .source_name, score: .score, snippet: .snippet}'
```



## Para recargar los servicios si se modifico algo

Posicionarse en infra/dev:
```bash
cd infra/dev
```
Ejecutar:
``` bash
docker compose down
docker compose up -d --build
```

## Para eliminar todo los datos en docker de este proyecto

```bash
cd infra/dev
docker compose down -v --rmi all

```