from loaders.docx_loader import load_docx


def load_local_document(path: str):
    """Carga un documento local. Este pipeline solo soporta DOCX."""
    if path.lower().endswith(".docx"):
        return load_docx(path)

    raise ValueError(f"Formato no soportado: {path}. Este pipeline solo acepta archivos .docx")
