def clean_text(text: str) -> str:
    if not text:
        return ""

    # Elimina caracteres NUL (PostgreSQL no los soporta)
    text = text.replace("\x00", "")
    text = text.replace("\u0000", "")
    text = text.strip()

    return text
