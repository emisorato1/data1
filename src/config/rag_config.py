from pydantic import BaseModel, Field


class RAGConfig(BaseModel):
    """
    Configuración calibrada del sistema RAG.
    Los parámetros han sido ajustados tras pruebas con el Entregable #5.
    """

    # Parámetros de Recuperación
    top_k: int = Field(default=5, description="Número de chunks iniciales a recuperar")
    similarity_threshold: float = Field(default=0.78, description="Umbral mínimo de similitud cosenoidal")

    # Parámetros de Reranking
    reranking_threshold: float = Field(
        default=0.85, description="Umbral de relevancia tras el paso de reranking cruzado"
    )

    # Parámetros de Chunking (Contexto)
    chunk_size: int = Field(default=512, description="Tamaño del chunk en tokens")
    chunk_overlap: int = Field(default=50, description="Solapamiento entre chunks en tokens")

    # Prompting - Personalidad del Banco
    system_prompt: str = Field(
        default=(
            "Eres un asistente virtual corporativo de un banco líder, diseñado para asistir a los clientes "
            "con empatía, profesionalismo y precisión extrema. "
            "Reglas estrictas:\n"
            "1. Basar tus respuestas ÚNICAMENTE en el contexto proporcionado. Si no sabes la respuesta o no está "
            "en el contexto, indica claramente: 'Lo siento, no tengo esa información en mis registros actuales.'\n"
            "2. Nunca inventes información financiera, tasas de interés, ni condiciones de productos.\n"
            "3. Mantén un tono formal pero accesible, priorizando la claridad y seguridad del usuario.\n"
            "4. Si el usuario menciona temas de fraude, robo de tarjetas o emergencias, instruye inmediatamente "
            "contactar al número de emergencias bancarias (0800-BANCO-EMERGENCIA) antes de "
            "dar cualquier otra información."
        ),
        description="System prompt base optimizado para el tono y personalidad del banco.",
    )


rag_config = RAGConfig()
