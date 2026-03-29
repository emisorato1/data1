"""BM25 full-text search: tsvector column, GIN index, trigger and hybrid_search SQL function.

Revision ID: 004
Revises: 003
Create Date: 2026-02-23

Agrega soporte BM25 a ``document_chunks`` y la función SQL ``hybrid_search``
que combina vector search con BM25 usando Reciprocal Rank Fusion (k=60).
Ver spec T4-S2-01 y ADR-007.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Columna tsvector para BM25
    # -------------------------------------------------------------------------
    op.execute(
        "ALTER TABLE document_chunks "
        "ADD COLUMN content_tsv tsvector "
        "GENERATED ALWAYS AS (to_tsvector('spanish', content)) STORED"
    )

    # -------------------------------------------------------------------------
    # 2. Índice GIN sobre content_tsv para búsquedas BM25 eficientes
    # -------------------------------------------------------------------------
    op.execute("CREATE INDEX ix_document_chunks_content_tsv ON document_chunks USING gin(content_tsv)")

    # -------------------------------------------------------------------------
    # 3. Función SQL hybrid_search con RRF (k=60)
    #
    #    Ejecuta vector search y BM25 en paralelo (CTEs), luego fusiona
    #    rankings con Reciprocal Rank Fusion.
    #
    #    Parámetros:
    #      p_embedding   halfvec — embedding normalizado de la query
    #      p_query_text  text    — texto de la query para BM25
    #      p_match_count int     — nº de chunks a retornar tras fusión
    #      p_rrf_k       int     — parámetro k de RRF (default 60)
    #      p_doc_ids     bigint[]— IDs de documentos accesibles (seguridad)
    # -------------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION hybrid_search(
            p_embedding    halfvec,
            p_query_text   text,
            p_match_count  int     DEFAULT 50,
            p_rrf_k        int     DEFAULT 60,
            p_doc_ids      bigint[] DEFAULT NULL
        )
        RETURNS TABLE (
            id            uuid,
            document_id   bigint,
            chunk_index   int,
            content       text,
            area          text,
            metadata      jsonb,
            document_name text,
            rrf_score     float8
        )
        LANGUAGE sql
        STABLE
        AS $$
        WITH
        -- ── Vector search: top-30 por cosine similarity ───────────────────
        vector_ranked AS (
            SELECT
                dc.id,
                dc.document_id,
                dc.chunk_index,
                dc.content,
                dc.area::text,
                dc.metadata,
                d.filename                                           AS document_name,
                1 - (dc.embedding <=> p_embedding)                  AS score,
                ROW_NUMBER() OVER (
                    ORDER BY dc.embedding <=> p_embedding
                )                                                    AS rank
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.is_active = true
              AND dc.embedding IS NOT NULL
              AND (p_doc_ids IS NULL OR dc.document_id = ANY(p_doc_ids))
            ORDER BY dc.embedding <=> p_embedding
            LIMIT 30
        ),

        -- ── BM25 search: top-30 por ts_rank_cd ───────────────────────────
        bm25_ranked AS (
            SELECT
                dc.id,
                dc.document_id,
                dc.chunk_index,
                dc.content,
                dc.area::text,
                dc.metadata,
                d.filename                                           AS document_name,
                ts_rank_cd(dc.content_tsv,
                    plainto_tsquery('spanish', p_query_text))       AS score,
                ROW_NUMBER() OVER (
                    ORDER BY ts_rank_cd(dc.content_tsv,
                        plainto_tsquery('spanish', p_query_text)) DESC
                )                                                    AS rank
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.is_active = true
              AND dc.content_tsv @@ plainto_tsquery('spanish', p_query_text)
              AND (p_doc_ids IS NULL OR dc.document_id = ANY(p_doc_ids))
            ORDER BY ts_rank_cd(
                dc.content_tsv,
                plainto_tsquery('spanish', p_query_text)
            ) DESC
            LIMIT 30
        ),

        -- ── Union de candidatos únicos ────────────────────────────────────
        all_chunks AS (
            SELECT id, document_id, chunk_index, content, area, metadata,
                   document_name
            FROM vector_ranked
            UNION
            SELECT id, document_id, chunk_index, content, area, metadata,
                   document_name
            FROM bm25_ranked
        ),

        -- ── RRF Fusion: score = Σ 1/(k + rank) ───────────────────────────
        rrf AS (
            SELECT
                ac.id,
                ac.document_id,
                ac.chunk_index,
                ac.content,
                ac.area,
                ac.metadata,
                ac.document_name,
                COALESCE(
                    1.0 / (p_rrf_k + vr.rank), 0.0
                ) + COALESCE(
                    1.0 / (p_rrf_k + br.rank), 0.0
                )                                                    AS rrf_score
            FROM all_chunks ac
            LEFT JOIN vector_ranked vr ON ac.id = vr.id
            LEFT JOIN bm25_ranked  br ON ac.id = br.id
        )

        SELECT
            id,
            document_id,
            chunk_index,
            content,
            area,
            metadata,
            document_name,
            rrf_score
        FROM rrf
        ORDER BY rrf_score DESC
        LIMIT p_match_count
        $$;
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS hybrid_search")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_content_tsv")
    op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS content_tsv")
