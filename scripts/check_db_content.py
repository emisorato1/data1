#!/usr/bin/env python3
"""Script para verificar contenido de la base de datos en Cloud SQL."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.infrastructure.database.connection import engine


async def check_database():
    """Verifica el contenido de la base de datos."""
    async with engine.begin() as conn:
        # Check documents
        result = await conn.execute(text("SELECT COUNT(*) FROM documents"))
        doc_count = result.scalar()
        print(f"📄 Documentos: {doc_count}")

        # Check chunks
        result = await conn.execute(text("SELECT COUNT(*) FROM chunks"))
        chunk_count = result.scalar()
        print(f"🧩 Chunks: {chunk_count}")

        # Check users
        result = await conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        print(f"👤 Usuarios: {user_count}")

        # Sample documents
        if doc_count > 0:
            result = await conn.execute(text("SELECT id, filename, created_at FROM documents LIMIT 5"))
            print("\n📋 Últimos documentos:")
            for row in result:
                print(f"  - {row.filename} (ID: {row.id}, creado: {row.created_at})")


if __name__ == "__main__":
    asyncio.run(check_database())
