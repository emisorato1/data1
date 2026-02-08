# 🚀 Enterprise AI Platform - Metadata Indexing Pipeline

Este servicio es el motor de extracción y procesamiento de datos estructurados del ECM (Content Server). Su objetivo es transformar la complejidad de las tablas de OpenText en un contrato de datos listo para la vectorización (RAG).

> **Nota Crítica:** Este desarrollo cumple estrictamente con el documento **Enterprise AI Platform – RAG Indexing Service**.

## 🏗️ Arquitectura Medallion

Implementamos una segregación de datos en tres capas para garantizar auditabilidad y reproducibilidad (Sección 1 de la documentación).

### 🥉 Capa 1_Bronze: Extracción Cruda
* **Propósito:** Es el "espejo" del sistema origen. No aplica lógica, solo persiste.
* **Componentes Clave:** * `extract_metadata.sql`: Query optimizada que unifica las 3 "islas" de OpenText (`DTreeCore`, `DVersData`, `ProviderData`).
    * **Extracción Incremental:** El sistema detecta automáticamente la fecha del último documento procesado para evitar duplicidad de trabajo.
* **Garantías:** Checksum SHA-256 del payload completo para auditoría (Sección 5).

### 🥈 Capa 2_Silver: Limpieza y Seguridad
* **Propósito:** Transformar datos SQL en información de negocio indexable.
* **Reglas de Negocio:**
    1. **Filtrado:** Solo se procesan MimeTypes permitidos (PDF, DOCX, TXT).
    2. **Seguridad Híbrida:** Conversión de la matriz de permisos ACL en **Security Tokens** con formato `Tipo:ID:Nivel` (Sección 5.6).
    3. **Estandarización:** Fechas convertidas a **ISO 8601**.

### 🥇 Capa 3_Gold: Contrato de Datos Final
* **Propósito:** Generar el payload inmutable para el ensamble con el Pipeline de Archivos.
* **Garantías:**
    * **Identidad:** IDs normalizados con formato `DOC-CS-{id}-v{version}`.
    * **Integridad:** `integrity_hash` individual por registro. Si el contenido o la seguridad cambian, el hash cambia.

---

## 📈 Trazabilidad y Linaje (Data Lineage)

Siguiendo la **Sección 4**, cada ejecución es rastreable mediante un `run_id` único.

| Artefacto Generado | Ubicación | Descripción |
| --- | --- | --- |
| **Bronze JSON** | `data/1_bronze/BRZ_{id}.json` | Datos SQL crudos + Metadata de extracción. |
| **Silver JSON** | `data/2_silver/SLV_{id}.json` | Documentos con seguridad resuelta y normalizados. |
| **Gold JSON** | `data/3_gold/GLD_{id}.json` | **Contrato Final**. Punto de entrada para la Vector DB. |

---

## 🛠️ Estructura del Módulo

Diseñado para ser integrado en el Monorepo corporativo:

```text
metadata-pipelines/
├── config/             # Variables .env (SERVER, DB_DRIVER, etc.)
├── data/               # "Data Lake" Local segregado
│   ├── 1_bronze/
│   ├── 2_silver/
│   └── 3_gold/
├── src/
│   ├── common/         # DatabaseManager, Utils y Logger
│   ├── pipeline/       # Lógica de las 3 capas Medallion
│   └── main.py         # Orquestador con lógica incremental
└── pyproject.toml      # Configuración de dependencias con uv

```

---

## 🤝 Instrucciones para el Pipeline de DATA

1. Utiliza el archivo generado en **`data/gold/GLD_{run_id}.json`**.
2. El campo `source_metadata.efs_path` contiene el nombre real del archivo en el Archive Center (ej: `103744.dat`).
3. El campo `document_id` es la clave primaria que debes usar para asociar tus vectores con nuestra metadata.

--- 

## 🛠️ Configuración del Entorno (Developer Setup)

Este proyecto utiliza **uv** para una gestión de dependencias ultra-rápida y determinística.

1. **Instalar uv** (si no lo tienes):
   `curl -LsSf https://astral.sh/uv/install.sh | sh`

2. **Instalar dependencias y crear venv**:
   `uv sync`

3. **Ejecutar el Pipeline**:
   `uv run src/main.py`
---

*Documentación técnica generada bajo estándares de alta criticidad.*

