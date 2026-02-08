from pypdf import PdfReader
from models.document import Document
 
def load_pdf(path: str) -> Document:
    reader = PdfReader(path)

    text = ""
    for page_number, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    metadata = {
        "source": path,
        "file_type": "pdf",
        "num_pages": len(reader.pages)
    }

    return Document(content=text, metadata=metadata)

