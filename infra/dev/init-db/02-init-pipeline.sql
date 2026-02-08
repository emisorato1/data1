-- ============================================================================
-- Enterprise AI Platform - Pipeline Tables Initialization
-- ============================================================================
-- Este script se ejecuta DESPUÉS de 01-init-extensions.sql
-- Añade las tablas necesarias para el pipeline de indexación PDFs
-- ============================================================================

-- 1. Registro de ejecuciones del pipeline (tabla auxiliar para tracking)
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(50) UNIQUE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running',
    documents_count INTEGER DEFAULT 0,
    chunks_count INTEGER DEFAULT 0
);

-- 2. Metadata extendida de documentos procesados por el pipeline
-- Esta tabla enlaza con la tabla 'documents' principal sin modificarla
CREATE TABLE IF NOT EXISTS document_pipeline_metadata (
    id                  SERIAL PRIMARY KEY,
    document_id         INTEGER NOT NULL,  -- Referencia manual a documents.id
    run_id              VARCHAR(50) REFERENCES pipeline_runs(run_id),
    data_id             INTEGER NOT NULL,  -- ID original del documento en la fuente
    name                VARCHAR(255) NOT NULL,
    mime_type           VARCHAR(100),
    file_size           INTEGER,
    visibility          VARCHAR(20) DEFAULT 'private',

    -- Bronze (ingesta raw)
    bronze_timestamp    TIMESTAMP WITH TIME ZONE,
    bronze_checksum     VARCHAR(64),
    bronze_status       VARCHAR(20),

    -- Silver (procesamiento texto)
    silver_timestamp    TIMESTAMP WITH TIME ZONE,
    silver_chars        INTEGER,
    silver_words        INTEGER,
    silver_tool         VARCHAR(50),
    silver_status       VARCHAR(20),

    -- Gold (chunking y embeddings)
    gold_timestamp      TIMESTAMP WITH TIME ZONE,
    gold_chunks_count   INTEGER,
    gold_status         VARCHAR(20),
    
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(run_id, data_id)
);

-- ============================================================================
-- INDICES
-- ============================================================================

-- Índice para buscar metadata por document_id
CREATE INDEX IF NOT EXISTS idx_document_pipeline_metadata_doc ON document_pipeline_metadata (document_id);

-- Índice para buscar por run_id
CREATE INDEX IF NOT EXISTS idx_document_pipeline_metadata_run ON document_pipeline_metadata (run_id);

-- Índice para buscar por data_id (ID original)
CREATE INDEX IF NOT EXISTS idx_document_pipeline_metadata_data ON document_pipeline_metadata (data_id);

-- Índice para filtrar por visibilidad
CREATE INDEX IF NOT EXISTS idx_document_pipeline_metadata_visibility ON document_pipeline_metadata (visibility);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE pipeline_runs IS 'Registro de ejecuciones del pipeline de indexación';

COMMENT ON TABLE document_pipeline_metadata IS 'Metadata extendida de documentos procesados (medallion: bronze/silver/gold)';

COMMENT ON COLUMN document_pipeline_metadata.visibility IS 'Control de acceso: public o private';

COMMENT ON COLUMN document_pipeline_metadata.bronze_timestamp IS 'Timestamp de ingesta raw del documento';

COMMENT ON COLUMN document_pipeline_metadata.silver_timestamp IS 'Timestamp de procesamiento de texto';

COMMENT ON COLUMN document_pipeline_metadata.gold_timestamp IS 'Timestamp de chunking y generación de embeddings';
