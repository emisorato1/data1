"""Configuration for topic classification guardrail.

Defines allowed/prohibited topics and few-shot examples for the
LLM-based topic classifier that deflects off-domain queries.
"""

from pydantic import BaseModel, Field


class TopicConfig(BaseModel):
    """Configurable topic classification parameters.

    Allows adjusting allowed/prohibited topics and the deflection
    response without code changes.
    """

    allowed_topics: list[str] = Field(
        default=[
            "productos bancarios (cuentas, tarjetas, prestamos, plazos fijos, CBU)",
            "operaciones bancarias (transferencias, pagos, alta, baja, apertura, cierre)",
            "procedimientos CAT (centro de atencion telefonica)",
            "politicas y normativas internas del banco",
            "regulaciones BCRA y circulares",
            "recursos humanos (vacaciones, licencias, sueldos, beneficios, capacitacion)",
            "documentacion interna y manuales",
            "seguridad bancaria y prevencion de fraude",
            "sistemas internos (COBIS, CRM)",
        ],
        description="Topics the assistant is allowed to answer about.",
    )

    prohibited_topics: list[str] = Field(
        default=[
            "deportes y resultados de partidos",
            "entretenimiento (peliculas, series, musica)",
            "politica y elecciones",
            "cocina y recetas",
            "consejos personales no bancarios",
            "programacion y tecnologia general",
            "salud y medicina (no laboral)",
            "viajes y turismo",
        ],
        description="Topics the assistant must deflect.",
    )

    deflection_response: str = Field(
        default=(
            "Esa consulta está fuera de mi área de conocimiento. "
            "Estoy preparado para responder preguntas sobre documentación "
            "bancaria interna, políticas, procedimientos y temas de RRHH."
        ),
        description="Polite response when deflecting off-topic queries.",
    )

    few_shot_examples: list[dict[str, str]] = Field(
        default=[
            {
                "query": "Cual es el procedimiento para abrir una cuenta corriente?",
                "classification": "ON_TOPIC",
            },
            {
                "query": "Necesito informacion sobre las licencias por maternidad",
                "classification": "ON_TOPIC",
            },
            {
                "query": "Que dice la circular del BCRA sobre encajes?",
                "classification": "ON_TOPIC",
            },
            {
                "query": "Como se hace una transferencia interbancaria?",
                "classification": "ON_TOPIC",
            },
            {
                "query": "Quien gano el partido de ayer?",
                "classification": "OFF_TOPIC:deportes, no relacionado con banca",
            },
            {
                "query": "Recomendame una pelicula para ver este fin de semana",
                "classification": "OFF_TOPIC:entretenimiento, no relacionado con banca",
            },
            {
                "query": "Cual es la mejor receta de empanadas?",
                "classification": "OFF_TOPIC:cocina, no relacionado con banca",
            },
            {
                "query": "Que opinas de las elecciones?",
                "classification": "OFF_TOPIC:politica, no relacionado con banca",
            },
            {
                "query": "Como hago torta?",
                "classification": "OFF_TOPIC:cocina, no relacionado con banca",
            },
            {
                "query": "Que tiempo hace hoy?",
                "classification": "OFF_TOPIC:clima, no relacionado con banca",
            },
            # --- Salud laboral (parece medico pero es RRHH) ---
            {
                "query": "Cual es el periodo maximo de reposo que puede indicar un certificado medico?",
                "classification": "ON_TOPIC",
            },
            {
                "query": "Cuales son los horarios del consultorio medico de Cordoba?",
                "classification": "ON_TOPIC",
            },
            # --- Beneficios corporativos con marcas externas ---
            {
                "query": "Cuantas lineas familiares puedo agregar al descuento de Movistar?",
                "classification": "ON_TOPIC",
            },
            {
                "query": "Que codigo de acceso uso para Samshop de Samsung?",
                "classification": "ON_TOPIC",
            },
            {
                "query": "Cuando se hace la convocatoria anual de becas?",
                "classification": "ON_TOPIC",
            },
            # --- Operaciones especificas de tarjeta ---
            {
                "query": "Que codigo de bloqueo se usa para el bloqueo preventivo de TD?",
                "classification": "ON_TOPIC",
            },
            {
                "query": "Como funciona esto?",
                "classification": "AMBIGUOUS:consulta demasiado generica sin contexto claro",
            },
            {
                "query": "Necesito ayuda",
                "classification": "AMBIGUOUS:consulta demasiado generica sin contexto claro",
            },
        ],
        description="Few-shot examples for the classifier prompt.",
    )


topic_config = TopicConfig()
