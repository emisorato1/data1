from loaders.pdf_loader import load_pdf


def load_local_document(path: str):
    if path.lower().endswith(".pdf"):
        return load_pdf(path)

    raise ValueError(f"Formato no soportado: {path}. Este pipeline solo acepta PDFs.")
