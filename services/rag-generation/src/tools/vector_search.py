"""Tool de búsqueda vectorial en pgvector.

Adaptado para trabajar con el esquema del servicio rag-indexation.
Los documentos se filtran por el campo metadata->>'description' que indica
si el documento es 'public' o 'private'.
"""

import os
from typing import Literal

import psycopg
from openai import OpenAI


# Cliente OpenAI singleton
_openai_client: OpenAI | None = None


def _get_openai_client() -> OpenAI:
    """Obtiene el cliente de OpenAI."""
    global _openai_client
    if _openai_client is None:
        api_key = os.environ["OPENAI_API_KEY"]
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def _get_embedding(text: str) -> list[float]:
    """Genera embedding para un texto usando OpenAI."""
    client = _get_openai_client()
    model = os.environ["EMBEDDING_MODEL"]
    
    response = client.embeddings.create(
        model=model,
        input=text
    )
    return response.data[0].embedding


def _get_connection() -> psycopg.Connection:
    """Crea conexión a PostgreSQL usando variables de entorno."""
    host = os.environ["PGVECTOR_HOST"]
    port = os.environ["PGVECTOR_PORT"]
    database = os.environ["PGVECTOR_DATABASE"]
    user = os.environ["PGVECTOR_USER"]
    password = os.environ["PGVECTOR_PASSWORD"]
    
    return psycopg.connect(
        host=host,
        port=int(port),
        dbname=database,
        user=user,
        password=password,
    )


def search_documents(
    query: str,
    document_type: Literal["public", "private"],
    k: int = 5,
    score_threshold: float = 0.4,
    department: str | None = None,
) -> list[dict]:

    # 1. Generar embedding de la consulta
    query_embedding = _get_embedding(query)
    
    # 2. Construir query SQL con búsqueda vectorial
    # Filtra por metadata->>'description' = document_type
    # La similitud coseno es: 1 - distancia
    sql = """
        SELECT 
            id,
            content,
            metadata,
            1 - (embedding <=> %s::vector) as similarity
        FROM documents
        WHERE metadata->>'description' = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    
    params = [
        query_embedding,
        document_type,
        query_embedding,
        k,
    ]
    
    # 3. Ejecutar búsqueda
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    finally:
        conn.close()
    
    # 4. Filtrar por umbral y formatear resultados
    documents = []
    for row in rows:
        doc_id, content, metadata, similarity = row
        
        # Asegurar que metadata sea un dict
        if metadata is None:
            metadata = {}
        
        if similarity >= score_threshold:
            # Extraer título: primero filename, luego source, luego title
            title = (
                metadata.get("filename") 
                or metadata.get("title") 
                or metadata.get("source", "").split("/")[-1] 
                or "Sin título"
            )
            
            documents.append({
                "document_id": str(doc_id),
                "chunk_id": str(metadata.get("chunk_id", doc_id)),
                "content": content,
                "title": title,
                "relevance_score": float(similarity),
                "metadata": metadata,
            })
    
    return documents
