"""RAG domain: documents, chunks, audit, pipeline_runs, OpenText security mirror

Revision ID: 002
Revises: 001
Create Date: 2026-02-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# ENUMs compartidos — SQLAlchemy los crea automaticamente con la primera tabla
area_funcional_enum = sa.Enum(
    "riesgos",
    "corporativo",
    "tesoreria",
    "cumplimiento",
    "operaciones",
    "tecnologia",
    "rrhh",
    "legal",
    "general",
    name="area_funcional",
)

security_event_type_enum = sa.Enum(
    "prompt_injection",
    "jailbreak",
    "pii_detected",
    "hallucination",
    "topic_out_of_bounds",
    "rate_limit",
    name="security_event_type",
)


def upgrade() -> None:
    # -- documents -------------------------------------------------------------
    # (area_funcional_enum se crea automaticamente aqui)
    op.create_table(
        "documents",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("file_hash", sa.String(64), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("area", area_funcional_enum, server_default="general", nullable=False),
        sa.Column("metadata", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("classification_level", sa.String(50), server_default=sa.text("'internal'"), nullable=True),
        sa.Column(
            "uploaded_by",
            sa.BigInteger(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_documents_uploaded_by", "documents", ["uploaded_by"])
    op.create_index("ix_documents_area", "documents", ["area"])
    op.create_index("ix_documents_file_hash", "documents", ["file_hash"])

    # -- document_chunks -------------------------------------------------------
    op.create_table(
        "document_chunks",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "document_id",
            sa.BigInteger(),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        # embedding halfvec(768) — se agrega via ALTER TABLE abajo
        sa.Column("area", area_funcional_enum, server_default="general", nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("metadata", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_area", "document_chunks", ["area"])

    # Columna embedding halfvec(768) via SQL raw (tipo nativo pgvector)
    op.execute("ALTER TABLE document_chunks ADD COLUMN embedding halfvec(768)")

    # Indice HNSW para busqueda vectorial cosine
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding ON document_chunks "
        "USING hnsw (embedding halfvec_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )

    # -- audit_logs ------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.BigInteger(), nullable=True),
        sa.Column("old_value", JSONB(), nullable=True),
        sa.Column("new_value", JSONB(), nullable=True),
        sa.Column("details", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("ip_address", INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), server_default=sa.text("'success'"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_user_time", "audit_logs", ["user_id", sa.text("created_at DESC")])
    op.create_index("ix_audit_resource", "audit_logs", ["resource_type", "resource_id"])
    op.create_index("ix_audit_action", "audit_logs", ["action"])
    op.create_index("ix_audit_request", "audit_logs", ["request_id"])

    # -- security_events -------------------------------------------------------
    # (security_event_type_enum se crea automaticamente aqui)
    op.create_table(
        "security_events",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", security_event_type_enum, nullable=False),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("rule_id", sa.String(100), nullable=True),
        sa.Column("severity", sa.String(20), server_default=sa.text("'medium'"), nullable=False),
        sa.Column("details", JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("ip_address", INET(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_security_events_user", "security_events", ["user_id", sa.text("created_at DESC")])
    op.create_index("ix_security_events_type", "security_events", ["event_type"])

    # -- pipeline_runs ---------------------------------------------------------
    op.create_table(
        "pipeline_runs",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "document_id",
            sa.BigInteger(),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dag_run_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_pipeline_runs_document_id", "pipeline_runs", ["document_id"])
    op.create_index("ix_pipeline_runs_status", "pipeline_runs", ["status"])

    # =========================================================================
    # ESPEJO OPENTEXT (Security Mirror) — schema public
    # =========================================================================

    # -- kuaf (usuarios y grupos OpenText) ------------------------------------
    op.create_table(
        "kuaf",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("type", sa.Integer(), nullable=True),
        sa.Column("deleted", sa.Integer(), server_default=sa.text("0"), nullable=True),
    )

    # -- kuafchildren (membresia de grupos) ------------------------------------
    op.create_table(
        "kuafchildren",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("group_id", sa.BigInteger(), nullable=False),
        sa.Column("child_id", sa.BigInteger(), nullable=False),
    )
    op.create_index("ix_kuafchildren_group_id", "kuafchildren", ["group_id"])
    op.create_index("ix_kuafchildren_child_id", "kuafchildren", ["child_id"])

    # -- dtree (jerarquia de documentos OpenText) ------------------------------
    op.create_table(
        "dtree",
        sa.Column("data_id", sa.BigInteger(), primary_key=True),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.Column("owner_id", sa.BigInteger(), nullable=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("sub_type", sa.Integer(), nullable=True),
    )
    op.create_index("ix_dtree_parent_id", "dtree", ["parent_id"])
    op.create_index("ix_dtree_owner_id", "dtree", ["owner_id"])

    # -- dtreeacl (ACL de documentos OpenText) ---------------------------------
    op.create_table(
        "dtreeacl",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("data_id", sa.BigInteger(), nullable=False),
        sa.Column("right_id", sa.BigInteger(), nullable=False),
        sa.Column("acl_type", sa.Integer(), nullable=True),
        sa.Column("permissions", sa.Integer(), nullable=True),
    )
    op.create_index("ix_dtreeacl_data_id", "dtreeacl", ["data_id"])
    op.create_index("ix_dtreeacl_right_id", "dtreeacl", ["right_id"])

    # -- dtreeancestors (jerarquia ancestral) ----------------------------------
    op.create_table(
        "dtreeancestors",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("data_id", sa.BigInteger(), nullable=False),
        sa.Column("ancestor_id", sa.BigInteger(), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=True),
    )
    op.create_index("ix_dtreeancestors_data_id", "dtreeancestors", ["data_id"])
    op.create_index("ix_dtreeancestors_ancestor_id", "dtreeancestors", ["ancestor_id"])

    # -- Vista Materializada: kuaf_membership_flat -----------------------------
    op.execute("""
        CREATE MATERIALIZED VIEW kuaf_membership_flat AS
        WITH RECURSIVE membership AS (
            SELECT id AS member_id, id AS group_id FROM kuaf WHERE deleted = 0
            UNION
            SELECT m.member_id, kc.group_id AS group_id
            FROM kuafchildren kc
            JOIN membership m ON kc.child_id = m.group_id
        )
        SELECT DISTINCT member_id, group_id FROM membership
    """)
    op.execute("CREATE INDEX ix_kuaf_flat_member ON kuaf_membership_flat(member_id)")
    op.execute("CREATE INDEX ix_kuaf_flat_group ON kuaf_membership_flat(group_id)")


def downgrade() -> None:
    # -- Vista Materializada ---------------------------------------------------
    op.execute("DROP MATERIALIZED VIEW IF EXISTS kuaf_membership_flat")

    # -- Espejo OpenText -------------------------------------------------------
    op.drop_table("dtreeancestors")
    op.drop_table("dtreeacl")
    op.drop_table("dtree")
    op.drop_table("kuafchildren")
    op.drop_table("kuaf")

    # -- Pipeline & Audit ------------------------------------------------------
    op.drop_table("pipeline_runs")
    op.drop_table("security_events")
    op.drop_table("audit_logs")

    # -- RAG Domain ------------------------------------------------------------
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding")
    op.drop_table("document_chunks")
    op.drop_table("documents")

    # -- ENUMs -----------------------------------------------------------------
    op.execute("DROP TYPE IF EXISTS security_event_type")
    op.execute("DROP TYPE IF EXISTS area_funcional")
