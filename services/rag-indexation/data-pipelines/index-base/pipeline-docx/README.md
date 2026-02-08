# Pipeline DOCX

Pipeline de ingesta de archivos `.docx` con chunking semántico y almacenamiento en PostgreSQL/pgvector.

## Instalación

```bash
cd pipeline-docx
python3 -m pip install -e .
```

## Uso

```bash
# Ingestar un archivo DOCX
python3 main.py ruta/al/archivo.docx

# O usar el archivo por defecto (data/raw/ejemplo.docx)
python3 main.py
```

## Configuración

Las variables de entorno se configuran en `.env`:

- `POSTGRES_HOST` - Host de PostgreSQL
- `POSTGRES_PORT` - Puerto de PostgreSQL  
- `POSTGRES_DB` - Nombre de la base de datos
- `POSTGRES_USER` - Usuario
- `POSTGRES_PASSWORD` - Contraseña

## Docker

```bash
docker-compose up -d
```
