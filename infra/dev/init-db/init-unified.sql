-- ============================================================================
-- Enterprise AI Platform - Database Initialization (UNIFIED)
-- ============================================================================
-- Este es el archivo unificado que contiene:
-- 1. Extensiones requeridas
-- 2. Esquema de autenticación y usuarios
-- 3. Esquema de mensajes y conversaciones
-- 4. Esquema de vector store para RAG
-- 5. Esquema de pipeline de indexación
-- 6. Todos los índices y datos iniciales
-- ============================================================================
-- Ejecución: Se ejecuta automáticamente al iniciar PostgreSQL por primera vez
-- Ubicación esperada: infra/dev/init-db/init.sql
-- ============================================================================

-- ============================================================================
-- EXTENSIONES NECESARIAS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- ESQUEMA PARA USUARIOS Y AUTENTICACION
-- ============================================================================

-- Tabla de tenants (multi-tenancy)
CREATE TABLE IF NOT EXISTS tenants (
    id uuid primary key default uuid_generate_v4(),
    name varchar(255) not null unique,
    status varchar(32) not null default 'active',
    config jsonb default '{}',
    is_active boolean default true,
    created_at timestamp with time zone default current_timestamp,
    updated_at timestamp with time zone default current_timestamp
);

-- Tabla de roles (compatible con ORM del API)
CREATE TABLE IF NOT EXISTS roles (
    id uuid primary key default uuid_generate_v4(),
    name varchar(64) not null unique,
    scopes jsonb not null default '[]'
);

-- Tabla de usuarios (compatible con ORM del API)
CREATE TABLE IF NOT EXISTS users (
    id uuid primary key default uuid_generate_v4(),
    email varchar(255) not null unique,
    password_hash varchar(255) not null,
    tenant_id uuid not null references tenants(id),
    role_id uuid not null references roles(id),
    is_active boolean not null default true,
    created_at timestamp with time zone default current_timestamp
);

-- Tabla de refresh tokens
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid references users(id) on delete cascade,
    token_hash varchar(255) not null unique,
    expires_at timestamp with time zone not null,
    created_at timestamp with time zone default current_timestamp,
    revoked_at timestamp with time zone
);

-- ============================================================================
-- ESQUEMA PARA CONVERSACIONES Y MENSAJES (API Gateway)
-- ============================================================================

-- Tabla de mensajes (simplificada, sin conversaciones separadas)
CREATE TABLE IF NOT EXISTS messages (
    id uuid primary key default uuid_generate_v4(),
    session_id uuid not null,
    user_role varchar(32) not null default 'public',
    direction varchar(16) not null,
    content text not null,
    meta jsonb default '{}' not null,
    created_at timestamp with time zone default current_timestamp
);

-- Tabla de sources para mensajes
CREATE TABLE IF NOT EXISTS message_sources (
    id uuid primary key default uuid_generate_v4(),
    message_id uuid references messages(id) on delete cascade,
    source_name varchar(500),
    snippet text,
    url text,
    score float,
    created_at timestamp with time zone default current_timestamp
);

-- ============================================================================
-- ESQUEMA PARA VECTOR STORE (RAG) - Compatible con rag-generation
-- ============================================================================
-- Esta tabla es usada directamente por el servicio rag-generation
-- El campo metadata->>'description' indica si es 'public' o 'private'

CREATE TABLE IF NOT EXISTS documents (
    id serial primary key,
    content text not null,
    embedding vector(1536),
    metadata jsonb default '{}'::jsonb,
    created_at timestamp with time zone default current_timestamp
);

-- ============================================================================
-- ESQUEMA PARA PIPELINE DE INDEXACION (RAG Indexing Service)
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
-- INDICES PARA PERFORMANCE
-- ============================================================================

-- Indices para busqueda de usuarios
CREATE INDEX IF NOT EXISTS idx_users_email on users(email);
CREATE INDEX IF NOT EXISTS idx_users_tenant on users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_role on users(role_id);

-- Indices para mensajes
CREATE INDEX IF NOT EXISTS idx_messages_session on messages(session_id);
CREATE INDEX IF NOT EXISTS idx_message_sources_message on message_sources(message_id);

-- Indice vectorial para busqueda semantica (HNSW)
CREATE INDEX IF NOT EXISTS idx_documents_embedding on documents 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Indice para filtrar por tipo de documento (public/private)
CREATE INDEX IF NOT EXISTS idx_documents_description on documents 
    ((metadata ->> 'description'));

-- Indices para pipeline de indexacion
CREATE INDEX IF NOT EXISTS idx_document_pipeline_metadata_doc on document_pipeline_metadata(document_id);
CREATE INDEX IF NOT EXISTS idx_document_pipeline_metadata_run on document_pipeline_metadata(run_id);
CREATE INDEX IF NOT EXISTS idx_document_pipeline_metadata_data on document_pipeline_metadata(data_id);
CREATE INDEX IF NOT EXISTS idx_document_pipeline_metadata_visibility on document_pipeline_metadata(visibility);

-- ============================================================================
-- DATOS INICIALES PARA DEMO
-- ============================================================================

-- Tenant por defecto
INSERT INTO tenants (id, name, config)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'default',
    '{"features": ["rag", "chat"]}'
) ON CONFLICT (name) DO NOTHING;

-- Roles basicos (nombres compatibles con RoleName enum del API)
INSERT INTO roles (id, name, scopes)
VALUES 
    (
        '00000000-0000-0000-0000-000000000001',
        'admin',
        '["read:all", "write:all", "admin:all"]'
    ),
    (
        '00000000-0000-0000-0000-000000000002',
        'private',
        '["read:public", "read:private", "write:conversations"]'
    ),
    (
        '00000000-0000-0000-0000-000000000003',
        'public',
        '["read:public", "write:conversations"]'
    )
ON CONFLICT (name) DO NOTHING;

-- NOTA: Los usuarios de prueba se crean via API usando el script:
-- python scripts/create_test_users.py
-- Esto asegura que los hashes de contraseña sean correctos (Argon2)

-- ============================================================================
-- COMENTARIOS Y DOCUMENTACION
-- ============================================================================

COMMENT ON TABLE tenants 
    IS 'Tabla de tenants para soporte multi-tenancy';

COMMENT ON TABLE roles 
    IS 'Roles predefinidos del sistema (admin, private, public)';

COMMENT ON TABLE users 
    IS 'Tabla de usuarios con referencias a tenant y role';

COMMENT ON TABLE refresh_tokens 
    IS 'Tokens de refresco JWT para mantener sesiones activas';

COMMENT ON TABLE messages 
    IS 'Historial de mensajes del chat (conversaciones)';

COMMENT ON TABLE message_sources 
    IS 'Fuentes citadas en las respuestas del asistente RAG';

COMMENT ON TABLE documents 
    IS 'Almacena documentos con embeddings para busqueda vectorial RAG';

COMMENT ON TABLE pipeline_runs 
    IS 'Registro de ejecuciones del pipeline de indexación de documentos';

COMMENT ON TABLE document_pipeline_metadata 
    IS 'Metadata extendida de documentos procesados (medallion: bronze/silver/gold)';

COMMENT ON COLUMN document_pipeline_metadata.visibility 
    IS 'Control de acceso: public o private';

COMMENT ON COLUMN document_pipeline_metadata.bronze_timestamp 
    IS 'Timestamp de ingesta raw del documento';

COMMENT ON COLUMN document_pipeline_metadata.silver_timestamp 
    IS 'Timestamp de procesamiento de texto';

COMMENT ON COLUMN document_pipeline_metadata.gold_timestamp 
    IS 'Timestamp de chunking y generación de embeddings';
