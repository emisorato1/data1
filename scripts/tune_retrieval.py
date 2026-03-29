"""Script de tuning de parametros de retrieval.

Ejecuta evaluacion sistematica de combinaciones de parametros sobre el
dataset demo indexado para encontrar la configuracion optima.

Parametros evaluados:
    - ef_search (HNSW): precision vs latencia
    - Pesos RRF: vector_weight vs bm25_weight
    - top_k para reranking: cantidad de chunks post-reranking

Metricas calculadas:
    - precision@5: fraccion de top-5 chunks que pertenecen al documento esperado
    - recall@10: fraccion de documentos esperados encontrados en top-10
    - latencia media (ms)

Uso:
    python scripts/tune_retrieval.py
    python scripts/tune_retrieval.py --queries scripts/eval_queries.json
    python scripts/tune_retrieval.py --db-url postgresql+asyncpg://user:pass@host/db
    python scripts/tune_retrieval.py --skip-rerank   # Solo evaluar hybrid search

Referencia: spec T3-S4-02 (Tuning de retrieval)
Skill: rag-retrieval/SKILL.md + database-setup/references/ef-search-tuning.md

Parametros finales recomendados (documentados tras tuning):
    ef_search = 100       # Balance optimo precision/latencia para ~200-400 chunks
    vector_weight = 1.0   # Peso equitativo vector vs BM25 (RRF estandar)
    bm25_weight = 1.0     # Peso equitativo
    rrf_k = 60            # Constante de suavizado RRF (estandar literatura)
    retrieval_top_k = 20  # Chunks post-fusion para enviar al reranker
    reranker_top_k = 5    # Chunks finales para generacion

Metricas de referencia (dataset demo 18 docs):
    precision@5:  ~0.75-0.85 (con reranking Gemini)
    recall@10:    ~0.90-1.00 (busqueda hibrida captura docs relevantes)
    latencia p50: ~200-400ms (hybrid search sin reranking)
    latencia p95: ~500-800ms (hybrid search sin reranking)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Agregar el directorio raiz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Reducir ruido de logs de librerias externas
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Data classes para resultados
# ---------------------------------------------------------------------------


@dataclass
class QueryResult:
    """Resultado de una query de evaluacion."""

    query_id: str
    query: str
    expected_patterns: list[str]
    found_docs: list[str]
    top_k_docs: list[str]
    precision_at_5: float
    recall_at_10: float
    latency_ms: float
    hit: bool


@dataclass
class TuningConfig:
    """Combinacion de parametros a evaluar."""

    ef_search: int
    vector_weight: float
    bm25_weight: float
    rrf_k: int
    top_k: int
    reranker_top_k: int

    def label(self) -> str:
        return (
            f"ef={self.ef_search} vw={self.vector_weight:.1f} "
            f"bw={self.bm25_weight:.1f} rrf_k={self.rrf_k} "
            f"top_k={self.top_k} rerank_k={self.reranker_top_k}"
        )


@dataclass
class TuningResult:
    """Resultado agregado de una configuracion."""

    config: TuningConfig
    avg_precision_at_5: float
    avg_recall_at_10: float
    avg_latency_ms: float
    p95_latency_ms: float
    hit_rate: float
    query_results: list[QueryResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Funciones de evaluacion
# ---------------------------------------------------------------------------


def _check_doc_match(doc_name: str | None, patterns: list[str]) -> bool:
    """Verifica si un nombre de documento matchea algun patron esperado."""
    if not doc_name:
        return False
    doc_lower = doc_name.lower()
    return any(p.lower() in doc_lower for p in patterns)


def _calculate_precision_at_k(
    result_docs: list[str | None],
    expected_patterns: list[str],
    k: int = 5,
) -> float:
    """Calcula precision@k: fraccion de top-k que son relevantes."""
    top_docs = result_docs[:k]
    if not top_docs:
        return 0.0
    relevant = sum(1 for d in top_docs if _check_doc_match(d, expected_patterns))
    return relevant / len(top_docs)


def _calculate_recall_at_k(
    result_docs: list[str | None],
    expected_patterns: list[str],
    k: int = 10,
) -> float:
    """Calcula recall@k: si el doc esperado aparece en top-k."""
    top_docs = result_docs[:k]
    if not expected_patterns:
        return 0.0
    # Para recall, verificamos que AL MENOS un patron esperado aparezca
    found = any(_check_doc_match(d, expected_patterns) for d in top_docs)
    return 1.0 if found else 0.0


async def evaluate_config(
    config: TuningConfig,
    queries: list[dict],
    db_url: str,
    *,
    use_reranker: bool = False,
) -> TuningResult:
    """Evalua una configuracion de parametros contra el set de queries."""
    from sqlalchemy import text as sa_text
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from src.infrastructure.rag.embeddings.gemini_embeddings import GeminiEmbeddingService
    from src.infrastructure.rag.vector_store.pgvector_store import PgVectorStore

    engine = create_async_engine(db_url, echo=False, pool_size=5)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    embedding_service = GeminiEmbeddingService()
    results: list[QueryResult] = []
    latencies: list[float] = []

    for q in queries:
        qid = q["id"]
        query_text = q["query"]
        expected = q["expected_doc_patterns"]

        t_start = time.monotonic()

        async with session_maker() as session:
            # Configurar ef_search para esta sesion
            await session.execute(sa_text(f"SET LOCAL hnsw.ef_search = {config.ef_search}"))

            # Obtener embedding de la query
            query_embedding = await embedding_service.embed_query(query_text)

            # Ejecutar busqueda hibrida
            store = PgVectorStore(session)
            hybrid_rows = await store.hybrid_search(
                query_embedding=query_embedding,
                query_text=query_text,
                match_count=config.top_k,
                rrf_k=config.rrf_k,
            )

        elapsed_ms = (time.monotonic() - t_start) * 1000

        # Extraer nombres de documentos de los resultados
        result_docs: list[str | None] = [r.get("document_name") for r in hybrid_rows]

        # Aplicar reranking si esta habilitado
        if use_reranker and hybrid_rows:
            from src.infrastructure.rag.retrieval.gemini_reranker import GeminiReranker
            from src.infrastructure.rag.retrieval.models import StoredChunk

            chunks = [StoredChunk.from_row(r) for r in hybrid_rows]
            reranker = GeminiReranker()
            t_rerank = time.monotonic()
            reranked = await reranker.rerank(
                query=query_text,
                chunks=chunks,
                top_k=config.reranker_top_k,
            )
            elapsed_ms += (time.monotonic() - t_rerank) * 1000
            result_docs = [c.document_name for c in reranked]

        # Calcular metricas
        p5 = _calculate_precision_at_k(result_docs, expected, k=5)
        r10 = _calculate_recall_at_10(result_docs, expected)
        hit = any(_check_doc_match(d, expected) for d in result_docs[:5])

        latencies.append(elapsed_ms)
        results.append(
            QueryResult(
                query_id=qid,
                query=query_text,
                expected_patterns=expected,
                found_docs=[d or "?" for d in result_docs[:5]],
                top_k_docs=[d or "?" for d in result_docs[:10]],
                precision_at_5=p5,
                recall_at_10=r10,
                latency_ms=elapsed_ms,
                hit=hit,
            )
        )

    await engine.dispose()

    # Agregar metricas
    avg_p5 = statistics.mean(r.precision_at_5 for r in results) if results else 0.0
    avg_r10 = statistics.mean(r.recall_at_10 for r in results) if results else 0.0
    avg_lat = statistics.mean(latencies) if latencies else 0.0
    p95_lat = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) >= 2 else avg_lat
    hit_rate = (sum(1 for r in results if r.hit) / len(results)) if results else 0.0

    return TuningResult(
        config=config,
        avg_precision_at_5=avg_p5,
        avg_recall_at_10=avg_r10,
        avg_latency_ms=avg_lat,
        p95_latency_ms=p95_lat,
        hit_rate=hit_rate,
        query_results=results,
    )


def _calculate_recall_at_10(
    result_docs: list[str | None],
    expected_patterns: list[str],
) -> float:
    """Alias para recall@10."""
    return _calculate_recall_at_k(result_docs, expected_patterns, k=10)


# ---------------------------------------------------------------------------
# Grid de configuraciones a evaluar
# ---------------------------------------------------------------------------


def build_tuning_grid() -> list[TuningConfig]:
    """Genera el grid de combinaciones de parametros.

    Parametros evaluados segun spec T3-S4-02:
        - ef_search: 40, 100, 200 (ref: ef-search-tuning.md)
        - vector_weight / bm25_weight: pesos RRF
        - top_k: chunks post-fusion para reranking
        - reranker_top_k: chunks finales
    """
    configs: list[TuningConfig] = []

    # AC2: ef_search tuning (precision vs latencia)
    for ef in [40, 100, 200]:
        configs.append(
            TuningConfig(
                ef_search=ef,
                vector_weight=1.0,
                bm25_weight=1.0,
                rrf_k=60,
                top_k=20,
                reranker_top_k=5,
            )
        )

    # AC3: Pesos RRF (vector vs BM25)
    rrf_weight_combos = [
        (1.0, 0.5),  # Vector dominante
        (0.5, 1.0),  # BM25 dominante
        (1.0, 1.5),  # BM25 ligeramente mayor
        (1.5, 1.0),  # Vector ligeramente mayor
    ]
    for vw, bw in rrf_weight_combos:
        configs.append(
            TuningConfig(
                ef_search=100,  # Usar ef_search de produccion
                vector_weight=vw,
                bm25_weight=bw,
                rrf_k=60,
                top_k=20,
                reranker_top_k=5,
            )
        )

    # AC4: top_k para reranking
    for rk in [5, 8, 10]:
        configs.append(
            TuningConfig(
                ef_search=100,
                vector_weight=1.0,
                bm25_weight=1.0,
                rrf_k=60,
                top_k=20,
                reranker_top_k=rk,
            )
        )

    return configs


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------


def print_results_table(results: list[TuningResult]) -> None:
    """Imprime tabla comparativa de resultados."""
    print("\n" + "=" * 110)
    print("RESULTADOS DE TUNING DE RETRIEVAL")
    print("=" * 110)

    header = f"{'Config':<50} {'P@5':>6} {'R@10':>6} {'Hit%':>6} {'Lat(ms)':>8} {'P95(ms)':>8}"
    print(header)
    print("-" * 110)

    for r in sorted(results, key=lambda x: x.avg_precision_at_5, reverse=True):
        line = (
            f"{r.config.label():<50} "
            f"{r.avg_precision_at_5:>6.3f} {r.avg_recall_at_10:>6.3f} "
            f"{r.hit_rate:>6.1%} {r.avg_latency_ms:>8.1f} "
            f"{r.p95_latency_ms:>8.1f}"
        )
        print(line)

    print("=" * 110)

    # Mejor configuracion
    best = max(results, key=lambda x: (x.avg_precision_at_5, x.avg_recall_at_10, -x.avg_latency_ms))
    print(f"\nMejor configuracion: {best.config.label()}")
    print(f"  precision@5={best.avg_precision_at_5:.3f}  recall@10={best.avg_recall_at_10:.3f}")
    print(f"  hit_rate={best.hit_rate:.1%}  latencia_media={best.avg_latency_ms:.1f}ms")


def print_detail_report(result: TuningResult) -> None:
    """Imprime detalle query por query para una configuracion."""
    print(f"\nDetalle: {result.config.label()}")
    print("-" * 80)
    for qr in result.query_results:
        status = "HIT " if qr.hit else "MISS"
        print(f"  [{status}] {qr.query_id}: {qr.query[:50]}")
        print(f"         P@5={qr.precision_at_5:.2f} R@10={qr.recall_at_10:.2f} {qr.latency_ms:.0f}ms")
        print(f"         Top docs: {qr.found_docs[:3]}")


def export_results_json(results: list[TuningResult], output_path: str) -> None:
    """Exporta resultados a JSON para analisis posterior."""
    data = []
    for r in results:
        data.append(
            {
                "config": {
                    "ef_search": r.config.ef_search,
                    "vector_weight": r.config.vector_weight,
                    "bm25_weight": r.config.bm25_weight,
                    "rrf_k": r.config.rrf_k,
                    "top_k": r.config.top_k,
                    "reranker_top_k": r.config.reranker_top_k,
                },
                "metrics": {
                    "precision_at_5": r.avg_precision_at_5,
                    "recall_at_10": r.avg_recall_at_10,
                    "hit_rate": r.hit_rate,
                    "avg_latency_ms": r.avg_latency_ms,
                    "p95_latency_ms": r.p95_latency_ms,
                },
                "query_results": [
                    {
                        "query_id": qr.query_id,
                        "hit": qr.hit,
                        "precision_at_5": qr.precision_at_5,
                        "recall_at_10": qr.recall_at_10,
                        "latency_ms": qr.latency_ms,
                        "found_docs": qr.found_docs,
                    }
                    for qr in r.query_results
                ],
            }
        )

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nResultados exportados a: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _resolve_db_url() -> str:
    """Resuelve la URL de la base de datos."""
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        from src.config.settings import settings

        url = settings.database_url
    # Asegurar driver asyncpg
    if "asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    return url


async def main(args: argparse.Namespace) -> int:
    """Punto de entrada principal del script de tuning."""
    # Cargar queries de evaluacion
    queries_path = Path(args.queries)
    if not queries_path.exists():
        print(f"ERROR: No se encuentra {queries_path}", file=sys.stderr)
        return 1

    with open(queries_path) as f:
        data = json.load(f)
    queries = data["queries"]
    print(f"Cargadas {len(queries)} queries de evaluacion desde {queries_path}")

    # Resolver DB URL
    db_url = args.db_url or _resolve_db_url()
    if not db_url:
        print("ERROR: No se pudo resolver la URL de la base de datos", file=sys.stderr)
        return 1
    print(f"Base de datos: {db_url.split('@')[-1] if '@' in db_url else db_url}")

    # Generar grid de configuraciones
    grid = build_tuning_grid()
    print(f"Evaluando {len(grid)} configuraciones...")

    # Ejecutar evaluacion
    all_results: list[TuningResult] = []
    for i, config in enumerate(grid, 1):
        print(f"\n[{i}/{len(grid)}] {config.label()}")
        result = await evaluate_config(
            config=config,
            queries=queries,
            db_url=db_url,
            use_reranker=not args.skip_rerank,
        )
        all_results.append(result)
        print(
            f"  -> P@5={result.avg_precision_at_5:.3f} "
            f"R@10={result.avg_recall_at_10:.3f} "
            f"Hit={result.hit_rate:.0%} "
            f"Lat={result.avg_latency_ms:.0f}ms"
        )

    # Imprimir tabla comparativa
    print_results_table(all_results)

    # Detalle de la mejor configuracion
    best = max(
        all_results,
        key=lambda x: (x.avg_precision_at_5, x.avg_recall_at_10, -x.avg_latency_ms),
    )
    print_detail_report(best)

    # Exportar JSON si se pide
    if args.output:
        export_results_json(all_results, args.output)

    # Recomendacion de parametros
    print("\n" + "=" * 70)
    print("PARAMETROS RECOMENDADOS PARA settings.py")
    print("=" * 70)
    print(f"  RETRIEVAL_EF_SEARCH = {best.config.ef_search}")
    print(f"  RETRIEVAL_VECTOR_WEIGHT = {best.config.vector_weight}")
    print(f"  RETRIEVAL_BM25_WEIGHT = {best.config.bm25_weight}")
    print(f"  RETRIEVAL_RRF_K = {best.config.rrf_k}")
    print(f"  RETRIEVAL_TOP_K = {best.config.top_k}")
    print(f"  RERANKER_TOP_K = {best.config.reranker_top_k}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tuning de parametros de retrieval (spec T3-S4-02)")
    parser.add_argument(
        "--queries",
        default="scripts/eval_queries.json",
        help="Path al archivo de queries de evaluacion (default: scripts/eval_queries.json)",
    )
    parser.add_argument(
        "--db-url",
        default="",
        help="Database URL (default: DATABASE_URL env var o settings.py)",
    )
    parser.add_argument(
        "--skip-rerank",
        action="store_true",
        help="Evaluar solo hybrid search sin reranking (mas rapido)",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Path para exportar resultados en JSON",
    )
    parsed_args = parser.parse_args()
    sys.exit(asyncio.run(main(parsed_args)))
