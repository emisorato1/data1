"""Seed data para desarrollo: usuarios mock, documentos mock, ACLs mock.

Uso:
    docker compose exec backend python -m scripts.seed_data
    # o directamente:
    python scripts/seed_data.py
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()
# Agregar raiz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "psycopg" in url:
        url = url.replace("psycopg", "asyncpg")
    return url


async def seed_users(session: AsyncSession) -> None:
    """Insertar usuarios mock (alineados con KUAF IDs)."""
    # Passwords: admin123!, analista123!, operador123!, auditor123!, tesorero123!
    await session.execute(
        text("""
        INSERT INTO users (id, email, hashed_password, full_name, is_active, is_superuser)
        VALUES
            (1000, 'admin@banco.com',
             '$2b$12$UA6R2c23z8qPEPwJSCzoHehYFGof7B48RcnPz/laSKL4TFz9hbx8.',
             'Admin Sistema', true, true),
            (1001, 'analista@banco.com',
             '$2b$12$Op8BIL6wKAw2mVflUeJau.0yCtM8JtEf9Ri0kio1rwzIP7QcvBJ9S',
             'Ana Lista Riesgos', true, false),
            (1002, 'operador@banco.com',
             '$2b$12$whdbfQx2TSQzVJj44HyEDeSCJuddsD/tcteSR3fd0JFrP9vCYGFcS',
             'Oscar Perador', true, false),
            (1003, 'auditor@banco.com',
             '$2b$12$JFw1LvoKpYU7aqcLrlfVS.nAIAoi0LP5YwFL2PP/h9C9pX3Tl3svy',
             'Audi Tor Cumpl', true, false),
            (1004, 'tesorero@banco.com',
             '$2b$12$r62hB2xs5HIaqe71AtCSV.KkxNMA8GcXSc8AJMz5129OOz5sUtlJS',
             'Teo Sorero', true, false)
        ON CONFLICT (id) DO NOTHING
    """)
    )
    print("  [OK] usuarios insertados")


async def seed_test_documents(session: AsyncSession) -> None:
    """Insertar documentos de demo escaneando tests/data/demo/ dinamicamente.

    Busca archivos .pdf y .docx reales en tests/data/demo/, los registra en la
    tabla documents con IDs a partir de 3000, y con file_path apuntando a
    /opt/airflow/data/demo/ (donde se montan via bind mount en el container).

    Archivos excluidos:
    - __init__.py, *.pyc (archivos Python)
    - invalid_file.* (fixtures de test negativo)
    - *.Zone.Identifier (metadatos de Windows)
    - Cualquier extension que no sea .pdf o .docx (el pipeline solo soporta esos)

    IDs reservados: 3000-3099 (rango de documentos de demo).
    """
    project_root = Path(__file__).resolve().parent.parent
    fixtures_dir = project_root / "tests" / "data" / "demo"
    container_base = "/opt/airflow/data/demo"

    # Extensiones que soporta el pipeline (FileValidator: PDF y DOCX por magic bytes)
    supported_extensions = {".pdf", ".docx"}

    # Archivos a excluir
    exclude_prefixes = ("invalid_", "__")
    exclude_suffixes = (".py", ".pyc", ".Zone.Identifier")

    if not fixtures_dir.exists():
        print("  [SKIP] tests/fixtures/ no encontrado")
        return

    # Recolectar archivos validos, ordenados por nombre para IDs deterministas
    valid_files = sorted(
        f
        for f in fixtures_dir.iterdir()
        if f.is_file()
        and f.suffix.lower() in supported_extensions
        and not f.name.startswith(exclude_prefixes)
        and not any(f.name.endswith(s) for s in exclude_suffixes)
    )

    if not valid_files:
        print("  [SKIP] No se encontraron archivos .pdf/.docx validos en tests/fixtures/")
        return

    base_id = 3000
    inserted = 0

    for idx, file_path in enumerate(valid_files):
        doc_id = base_id + idx
        filename = file_path.name
        container_path = f"{container_base}/{filename}"
        file_type = file_path.suffix.lstrip(".").lower()
        file_size = file_path.stat().st_size

        await session.execute(
            text("""
                INSERT INTO documents (id, filename, file_path, file_type, file_size, area, uploaded_by)
                VALUES (:id, :filename, :file_path, :file_type, :file_size, 'general', 1000)
                ON CONFLICT (id) DO UPDATE SET
                    filename = EXCLUDED.filename,
                    file_path = EXCLUDED.file_path,
                    file_type = EXCLUDED.file_type,
                    file_size = EXCLUDED.file_size
            """),
            {
                "id": doc_id,
                "filename": filename,
                "file_path": container_path,
                "file_type": file_type,
                "file_size": file_size,
            },
        )

        # --- Permission mirror entries (dtree, dtreeacl, dtreeancestors) ---
        # Place test docs under "General" folder (105), matching area='general'.
        # Grant all groups SeeContents (bitmask 2) + Admin full (65535),
        # same pattern as General docs 2017-2019 in seed_dtreeacl().
        await session.execute(
            text("""
                INSERT INTO dtree (data_id, parent_id, owner_id, name, sub_type)
                VALUES (:data_id, 105, 1000, :name, 144)
                ON CONFLICT (data_id) DO NOTHING
            """),
            {"data_id": doc_id, "name": filename},
        )
        await session.execute(
            text("""
                INSERT INTO dtreeacl (data_id, right_id, acl_type, permissions)
                VALUES
                    (:did, 5000, 3, 2),
                    (:did, 5001, 3, 2),
                    (:did, 5002, 3, 2),
                    (:did, 5003, 3, 2),
                    (:did, 5004, 3, 65535)
                ON CONFLICT DO NOTHING
            """),
            {"did": doc_id},
        )
        await session.execute(
            text("""
                INSERT INTO dtreeancestors (data_id, ancestor_id, depth)
                VALUES
                    (:did, 105, 1),
                    (:did, 100, 2)
                ON CONFLICT DO NOTHING
            """),
            {"did": doc_id},
        )

        inserted += 1
        print(f"    ID {doc_id}: {filename} ({file_size} bytes) -> {container_path}")

    print(f"  [OK] {inserted} documentos de prueba insertados con ACLs (IDs {base_id}-{base_id + inserted - 1})")


async def seed_kuaf(session: AsyncSession) -> None:
    """Insertar entidades OpenText mock (usuarios y grupos)."""
    await session.execute(
        text("""
        INSERT INTO kuaf (id, name, type, deleted)
        VALUES
            -- Usuarios (type=0)
            (1000, 'admin',       0, 0),
            (1001, 'analista',    0, 0),
            (1002, 'operador',    0, 0),
            (1003, 'auditor',     0, 0),
            (1004, 'tesorero',    0, 0),
            -- Grupos/Roles (type=1)
            (5000, 'Riesgos',       1, 0),
            (5001, 'Operaciones',   1, 0),
            (5002, 'Cumplimiento',  1, 0),
            (5003, 'Tesoreria',     1, 0),
            (5004, 'Administracion',1, 0)
        ON CONFLICT (id) DO NOTHING
    """)
    )
    print("  [OK] kuaf (usuarios/grupos OpenText) insertados")


async def seed_kuafchildren(session: AsyncSession) -> None:
    """Insertar membresias de grupos OpenText mock."""
    await session.execute(
        text("""
        INSERT INTO kuafchildren (group_id, child_id)
        VALUES
            -- analista pertenece a Riesgos
            (5000, 1001),
            -- operador pertenece a Operaciones
            (5001, 1002),
            -- auditor pertenece a Cumplimiento
            (5002, 1003),
            -- tesorero pertenece a Tesoreria
            (5003, 1004),
            -- admin pertenece a Administracion
            (5004, 1000),
            -- admin tambien en todos los grupos
            (5000, 1000),
            (5001, 1000),
            (5002, 1000),
            (5003, 1000)
        ON CONFLICT DO NOTHING
    """)
    )
    print("  [OK] kuafchildren (membresias) insertadas")


async def seed_dtree(session: AsyncSession) -> None:
    """Insertar jerarquia de carpetas OpenText mock."""
    await session.execute(
        text("""
        INSERT INTO dtree (data_id, parent_id, owner_id, name, sub_type)
        VALUES
            -- Carpetas raiz (sub_type=0)
            (100, NULL, 1000, 'Documentos Banco', 0),
            (101, 100,  1000, 'Riesgos',          0),
            (102, 100,  1000, 'Operaciones',       0),
            (103, 100,  1000, 'Cumplimiento',      0),
            (104, 100,  1000, 'Tesoreria',         0),
            (105, 100,  1000, 'General',           0)
        ON CONFLICT (data_id) DO NOTHING
    """)
    )
    print("  [OK] dtree (jerarquia carpetas OpenText) insertada")


async def seed_dtreeacl(session: AsyncSession) -> None:
    """Insertar ACLs OpenText mock. Los documentos de demo reciben sus ACLs en seed_test_documents."""
    # Las ACLs de documentos se insertan dinamicamente en seed_test_documents()
    # junto con cada documento de tests/data/demo/
    print("  [OK] dtreeacl (permisos OpenText) — gestionados por seed_test_documents")


async def seed_dtreeancestors(session: AsyncSession) -> None:
    """Insertar jerarquia ancestral de carpetas para Chinese Walls."""
    await session.execute(
        text("""
        INSERT INTO dtreeancestors (data_id, ancestor_id, depth)
        VALUES
            -- Carpetas -> raiz
            (101, 100, 1),
            (102, 100, 1),
            (103, 100, 1),
            (104, 100, 1),
            (105, 100, 1)
        ON CONFLICT DO NOTHING
    """)
    )
    print("  [OK] dtreeancestors (jerarquia carpetas) insertados")


async def refresh_materialized_view(session: AsyncSession) -> None:
    """Refrescar la vista materializada de membresia."""
    await session.execute(text("REFRESH MATERIALIZED VIEW kuaf_membership_flat"))
    print("  [OK] kuaf_membership_flat refrescada")


async def seed_all() -> None:
    """Ejecutar todo el seed data."""
    engine = create_async_engine(_get_database_url(), echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=== Seed Data para Desarrollo ===\n")

    async with async_session() as session, session.begin():
        await seed_users(session)
        await seed_test_documents(session)
        await seed_kuaf(session)
        await seed_kuafchildren(session)
        await seed_dtree(session)
        await seed_dtreeacl(session)
        await seed_dtreeancestors(session)
        await refresh_materialized_view(session)

    await engine.dispose()
    print("\n=== Seed completado ===")


if __name__ == "__main__":
    asyncio.run(seed_all())
