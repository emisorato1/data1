"""
Chunking determinístico por tamaño fijo con overlap.
No depende de modelos externos - 100% reproducible.
"""

from config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list[str]:
    """
    Divide el texto en chunks de tamaño fijo con overlap.
    
    Args:
        text: Texto a dividir
        chunk_size: Tamaño de cada chunk en caracteres (default: config)
        overlap: Solapamiento entre chunks (default: config)
    
    Returns:
        Lista de chunks
    """
    if not text or not text.strip():
        return []
    
    if chunk_size is None:
        chunk_size = CHUNK_SIZE
    if overlap is None:
        overlap = CHUNK_OVERLAP
    
    # Limpiar texto
    text = text.strip()
    
    # Si el texto es menor al chunk_size, devolver como único chunk
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Si no es el último chunk, intentar cortar en un buen punto
        if end < len(text):
            # Buscar el último salto de párrafo, línea, o punto
            for sep in ["\n\n", "\n", ". ", " "]:
                last_sep = text.rfind(sep, start, end)
                if last_sep > start:
                    end = last_sep + len(sep)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Avanzar con overlap
        start = end - overlap if end < len(text) else len(text)
    
    return chunks


# Alias para compatibilidad
def semantic_chunk(text: str, **kwargs) -> list[str]:
    """Alias para mantener compatibilidad con código existente."""
    return chunk_text(text)
