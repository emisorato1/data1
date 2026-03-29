-- =============================================================================
-- Init script para PostgreSQL — se ejecuta solo en la primera creacion del volumen
-- =============================================================================

-- Extensiones requeridas por el sistema RAG
CREATE EXTENSION IF NOT EXISTS vector;       -- pgvector: embeddings y busqueda vectorial
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- generacion de UUIDs
CREATE EXTENSION IF NOT EXISTS pg_trgm;      -- trigram index para busqueda BM25/full-text
