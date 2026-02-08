-- ============================================================================
-- Enterprise AI Platform - Database Initialization
-- ============================================================================
-- Este script se ejecuta automaticamente al iniciar PostgreSQL por primera vez
-- ============================================================================

-- Habilitar extensiones necesarias
create extension if not exists "uuid-ossp";

create extension if not exists "vector";

-- ============================================================================
-- ESQUEMA PARA USUARIOS Y AUTENTICACION
-- ============================================================================

-- Tabla de tenants (multi-tenancy)
create table if not exists tenants (
    id uuid primary key default uuid_generate_v4 (),
    name varchar(255) not null unique,
    status varchar(32) not null default 'active',
    config jsonb default '{}',
    is_active boolean default true,
    created_at timestamp
    with
        time zone default current_timestamp,
        updated_at timestamp
    with
        time zone default current_timestamp
);

-- Tabla de roles (compatible con ORM del API)
create table if not exists roles (
    id uuid primary key default uuid_generate_v4 (),
    name varchar(64) not null unique,
    scopes jsonb not null default '[]'
);

-- Tabla de usuarios (compatible con ORM del API)
create table if not exists users (
    id uuid primary key default uuid_generate_v4 (),
    email varchar(255) not null unique,
    password_hash varchar(255) not null,
    tenant_id uuid not null references tenants (id),
    role_id uuid not null references roles (id),
    is_active boolean not null default true,
    created_at timestamp
    with
        time zone default current_timestamp
);

-- Tabla de refresh tokens
create table if not exists refresh_tokens (
    id uuid primary key default uuid_generate_v4 (),
    user_id uuid references users (id) on delete cascade,
    token_hash varchar(255) not null unique,
    expires_at timestamp
    with
        time zone not null,
        created_at timestamp
    with
        time zone default current_timestamp,
        revoked_at timestamp
    with
        time zone
);

-- ============================================================================
-- ESQUEMA PARA CONVERSACIONES Y MENSAJES (API Gateway)
-- ============================================================================

-- Tabla de mensajes (simplificada, sin conversaciones separadas)
create table if not exists messages (
    id uuid primary key default uuid_generate_v4 (),
    session_id uuid not null,
    user_role varchar(32) not null default 'public',
    direction varchar(16) not null,
    content text not null,
    meta jsonb default '{}' not null,
    created_at timestamp
    with
        time zone default current_timestamp
);

-- Tabla de sources para mensajes
create table if not exists message_sources (
    id uuid primary key default uuid_generate_v4 (),
    message_id uuid references messages (id) on delete cascade,
    source_name varchar(500),
    snippet text,
    url text,
    score float,
    created_at timestamp
    with
        time zone default current_timestamp
);

-- ============================================================================
-- ESQUEMA PARA VECTOR STORE (RAG) - Compatible con rag-generation
-- ============================================================================
-- Esta tabla es usada directamente por el servicio rag-generation
-- El campo metadata->>'description' indica si es 'public' o 'private'

create table if not exists documents (
    id serial primary key,
    content text not null,
    embedding vector(1536),
    metadata jsonb default '{}'::jsonb,
    created_at timestamp with time zone default current_timestamp
);

-- ============================================================================
-- INDICES PARA PERFORMANCE
-- ============================================================================

-- Indices para busqueda de usuarios
create index if not exists idx_users_email on users (email);

create index if not exists idx_users_tenant on users (tenant_id);

create index if not exists idx_users_role on users (role_id);

-- Indices para mensajes
create index if not exists idx_messages_session on messages (session_id);

create index if not exists idx_message_sources_message on message_sources (message_id);

-- Indice vectorial para busqueda semantica (HNSW)
create index if not exists idx_documents_embedding on documents using hnsw (embedding vector_cosine_ops)
with (m = 16, ef_construction = 64);

-- Indice para filtrar por tipo de documento (public/private)
create index if not exists idx_documents_description on documents ((metadata ->> 'description'));

-- ============================================================================
-- DATOS INICIALES PARA DEMO
-- ============================================================================

-- Tenant por defecto
insert into
    tenants (id, name, config)
values (
        '00000000-0000-0000-0000-000000000001',
        'default',
        '{"features": ["rag", "chat"]}'
    ) on conflict (name) do nothing;

-- Roles basicos (nombres compatibles con RoleName enum del API)
insert into
    roles (id, name, scopes)
values (
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
    ) on conflict (name) do nothing;

-- NOTA: Los usuarios de prueba se crean via API usando el script:
-- python scripts/create_test_users.py
-- Esto asegura que los hashes de contraseña sean correctos (Argon2)

-- ============================================================================
-- COMENTARIOS
-- ============================================================================

comment on
table documents is 'Almacena documentos con embeddings para busqueda vectorial RAG';

comment on table messages is 'Historial de mensajes del chat';

comment on
table message_sources is 'Fuentes citadas en las respuestas del asistente';