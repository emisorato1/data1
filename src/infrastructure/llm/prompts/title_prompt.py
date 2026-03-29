"""Prompt templates for generating conversation titles."""

TITLE_GENERATION_PROMPT = """\
Genera un título corto y conciso (máximo 4 a 5 palabras) para la siguiente conversación \
basado en el primer mensaje del usuario.
No uses comillas, puntos finales ni texto adicional, solo el título.

Mensaje del usuario: "{message}"
Título:"""
