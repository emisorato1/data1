"""Script de verificacion del dataset demo indexado.

Verifica que los documentos demo fueron correctamente indexados consultando
la base de datos y ejecutando queries de ejemplo contra el sistema de
busqueda hibrida.

Uso:
    python scripts/verify_demo_data.py
    python scripts/verify_demo_data.py --db-url postgresql://user:pass@host:5432/db
    python scripts/verify_demo_data.py --queries-only  # Solo ejecuta queries de ejemplo

Referencia: spec T3-S4-01 (Carga masiva dataset demo via Airflow)
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# ---------------------------------------------------------------------------
# Queries de ejemplo para verificar relevancia
# ---------------------------------------------------------------------------
EXAMPLE_QUERIES = [
    {
        "query": "Cuales son las medidas disponibles para las cajas de seguridad?",
        "expected_doc_pattern": "CS001",
        "area": "general",
    },
    {
        "query": "Que es un paquete de productos y que beneficios tiene?",
        "expected_doc_pattern": "PAQ001",
        "area": "general",
    },
    {
        "query": "Como solicitar la baja de un paquete de productos?",
        "expected_doc_pattern": "baja de paquete",
        "area": "general",
    },
    {
        "query": "Como retener a un cliente que quiere cancelar su paquete?",
        "expected_doc_pattern": "Retenci",
        "area": "general",
    },
    {
        "query": "Como dar de alta un paquete en el sistema Cobis?",
        "expected_doc_pattern": "Alta de Paquete",
        "area": "general",
    },
    {
        "query": "Como hacer un upgrade de paquete en el sistema?",
        "expected_doc_pattern": "Upgrade de Paquete",
        "area": "general",
    },
    {
        "query": "Cuales son los requisitos para un prestamo hipotecario UVA?",
        "expected_doc_pattern": "PP001",
        "area": "general",
    },
    {
        "query": "Como se otorga un prestamo personal desde el Contact Center?",
        "expected_doc_pattern": "Otorgamiento",
        "area": "general",
    },
    {
        "query": "Como pagar la cuota de un prestamo personal por CRM?",
        "expected_doc_pattern": "Pago de cuota",
        "area": "general",
    },
    {
        "query": "Como denunciar un accidente de trabajo?",
        "expected_doc_pattern": "Salud",
        "area": "general",
    },
]


def get_db_connection(db_url: str):
    """Create a sync psycopg connection."""
    import psycopg

    url = db_url
    if "+psycopg" in url:
        url = url.replace("+psycopg", "")
    elif "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    return psycopg.connect(url)


def verify_indexed_documents(db_url: str) -> dict:
    """Query the DB for indexed demo documents and return metrics."""
    conn = get_db_connection(db_url)
    metrics = {}

    try:
        with conn.cursor() as cur:
            # Total documents from demo load
            cur.execute(
                """
                SELECT COUNT(*) FROM documents
                WHERE metadata->>'source' = 'demo_batch_load' AND is_active = true
                """
            )
            row = cur.fetchone()
            metrics["total_documents"] = row[0] if row else 0

            # Document details
            cur.execute(
                """
                SELECT d.id, d.filename, d.file_type, d.file_size,
                       (d.metadata->'indexing'->>'chunk_count')::int as chunk_count,
                       (d.metadata->'indexing'->>'total_tokens')::int as total_tokens,
                       d.metadata->'indexing'->'areas' as areas
                FROM documents d
                WHERE d.metadata->>'source' = 'demo_batch_load' AND d.is_active = true
                ORDER BY d.filename
                """
            )
            documents = []
            for r in cur.fetchall():
                doc = {
                    "id": r[0],
                    "filename": r[1],
                    "file_type": r[2],
                    "file_size": r[3],
                    "chunk_count": r[4] or 0,
                    "total_tokens": r[5] or 0,
                    "areas": r[6] or {},
                }
                documents.append(doc)
            metrics["documents"] = documents

            # Total chunks
            cur.execute(
                """
                SELECT COUNT(*), SUM(token_count), AVG(token_count),
                       MIN(token_count), MAX(token_count)
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.metadata->>'source' = 'demo_batch_load' AND d.is_active = true
                """
            )
            row = cur.fetchone()
            if row and row[0]:
                metrics["chunks"] = {
                    "total": row[0],
                    "total_tokens": int(row[1]) if row[1] else 0,
                    "avg_tokens": round(float(row[2]), 1) if row[2] else 0,
                    "min_tokens": int(row[3]) if row[3] else 0,
                    "max_tokens": int(row[4]) if row[4] else 0,
                }
            else:
                metrics["chunks"] = {"total": 0}

            # Chunks per area
            cur.execute(
                """
                SELECT dc.area, COUNT(*), SUM(dc.token_count)
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.metadata->>'source' = 'demo_batch_load' AND d.is_active = true
                GROUP BY dc.area
                ORDER BY COUNT(*) DESC
                """
            )
            metrics["areas"] = {r[0]: {"chunks": r[1], "tokens": int(r[2]) if r[2] else 0} for r in cur.fetchall()}

            # Pipeline runs
            cur.execute(
                """
                SELECT pr.status, COUNT(*)
                FROM pipeline_runs pr
                JOIN documents d ON pr.document_id = d.id
                WHERE d.metadata->>'source' = 'demo_batch_load'
                GROUP BY pr.status
                """
            )
            metrics["pipeline_runs"] = {r[0]: r[1] for r in cur.fetchall()}

    finally:
        conn.close()

    return metrics


def verify_queries(db_url: str) -> list[dict]:
    """Execute example queries using BM25 text search and check relevance."""
    conn = get_db_connection(db_url)
    results = []

    try:
        with conn.cursor() as cur:
            for q in EXAMPLE_QUERIES:
                # Simple text search (BM25-style via tsvector if available, fallback to ILIKE)
                cur.execute(
                    """
                    SELECT dc.content, d.filename, dc.token_count,
                           ts_rank(to_tsvector('spanish', dc.content),
                                   plainto_tsquery('spanish', %s)) as rank
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    WHERE d.metadata->>'source' = 'demo_batch_load'
                      AND d.is_active = true
                      AND to_tsvector('spanish', dc.content) @@ plainto_tsquery('spanish', %s)
                    ORDER BY rank DESC
                    LIMIT 3
                    """,
                    (q["query"], q["query"]),
                )
                rows = cur.fetchall()

                # Check if results match expected pattern
                matched = False
                top_results = []
                for r in rows:
                    content_preview = r[0][:100] + "..." if len(r[0]) > 100 else r[0]
                    filename = r[1]
                    top_results.append(
                        {
                            "filename": filename,
                            "tokens": r[2],
                            "rank": round(float(r[3]), 4),
                            "preview": content_preview,
                        }
                    )
                    if q["expected_doc_pattern"].lower() in filename.lower():
                        matched = True

                results.append(
                    {
                        "query": q["query"],
                        "expected_pattern": q["expected_doc_pattern"],
                        "matched": matched,
                        "results_count": len(rows),
                        "top_results": top_results,
                    }
                )

    finally:
        conn.close()

    return results


def print_report(metrics: dict, query_results: list[dict] | None = None) -> None:
    """Print a formatted verification report."""
    print("=" * 70)
    print("VERIFICACION DEL DATASET DEMO")
    print("=" * 70)

    # Documents
    print(f"\nDocumentos indexados: {metrics.get('total_documents', 0)}")
    if metrics.get("documents"):
        print(f"\n{'Archivo':<50} {'Chunks':>7} {'Tokens':>8}")
        print("-" * 70)
        for doc in metrics["documents"]:
            print(f"  {doc['filename']:<48} {doc['chunk_count']:>7} {doc['total_tokens']:>8}")

    # Chunks
    chunks = metrics.get("chunks", {})
    if chunks.get("total", 0) > 0:
        print(f"\nTotal chunks:   {chunks['total']}")
        print(f"Total tokens:   {chunks.get('total_tokens', 'N/A')}")
        print(f"Avg tokens:     {chunks.get('avg_tokens', 'N/A')}")
        print(f"Min tokens:     {chunks.get('min_tokens', 'N/A')}")
        print(f"Max tokens:     {chunks.get('max_tokens', 'N/A')}")

    # Areas
    areas = metrics.get("areas", {})
    if areas:
        print("\nDistribucion por area funcional:")
        for area, stats in areas.items():
            print(f"  {area:<20} {stats['chunks']:>5} chunks  {stats['tokens']:>8} tokens")

    # Pipeline runs
    runs = metrics.get("pipeline_runs", {})
    if runs:
        print(f"\nPipeline runs: {runs}")

    # Query verification
    if query_results:
        print(f"\n{'=' * 70}")
        print("VERIFICACION DE QUERIES")
        print(f"{'=' * 70}")

        passed = sum(1 for r in query_results if r["matched"])
        total = len(query_results)
        print(f"\nQueries relevantes: {passed}/{total}")

        for r in query_results:
            status = "OK" if r["matched"] else "MISS"
            print(f"\n  [{status}] {r['query']}")
            print(f"       Patron esperado: {r['expected_pattern']}")
            print(f"       Resultados: {r['results_count']}")
            if r["top_results"]:
                for tr in r["top_results"][:2]:
                    print(f"         -> {tr['filename']} (rank={tr['rank']})")

    print(f"\n{'=' * 70}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Verify demo dataset indexing")
    parser.add_argument(
        "--db-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="Database URL (default: DATABASE_URL env var)",
    )
    parser.add_argument(
        "--queries-only",
        action="store_true",
        help="Only run query verification (skip document metrics)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of formatted report",
    )
    args = parser.parse_args()

    if not args.db_url:
        print("ERROR: No database URL provided. Set DATABASE_URL or use --db-url", file=sys.stderr)
        return 1

    try:
        metrics = {}
        query_results = None

        if not args.queries_only:
            metrics = verify_indexed_documents(args.db_url)

        query_results = verify_queries(args.db_url)

        if args.json:
            output = {"metrics": metrics, "query_results": query_results}
            print(json.dumps(output, indent=2, default=str))
        else:
            print_report(metrics, query_results)

        # Exit code: 0 if all queries matched, 1 if any failed
        if query_results:
            all_matched = all(r["matched"] for r in query_results)
            return 0 if all_matched else 1
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
