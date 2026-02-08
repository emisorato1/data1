"""
Loader para descargar documentos desde OpenText Content Server.

Uso:
    from loaders.opentext_loader import load_from_opentext
    
    doc = load_from_opentext(data_id=103830)
"""

import os
import io
import requests
from pypdf import PdfReader
from models.document import Document


# Config desde env
OTCS_BASE_URL = os.getenv("OTCS_BASE_URL", "http://192.168.68.22/OTCS/cs.exe")
OTCS_USERNAME = os.getenv("OTCS_USERNAME", "otadmin@otds.admin")
OTCS_PASSWORD = os.getenv("OTCS_PASSWORD", "inicio1234.")
OTCS_TIMEOUT = int(os.getenv("OTCS_TIMEOUT", "60"))


def _get_auth_ticket() -> str:
    """Obtiene el ticket de autenticación de Content Server."""
    url = f"{OTCS_BASE_URL}/api/v1/auth"
    
    response = requests.post(
        url,
        data={"username": OTCS_USERNAME, "password": OTCS_PASSWORD},
        timeout=OTCS_TIMEOUT,
        verify=False,
    )
    response.raise_for_status()
    
    data = response.json()
    return data.get("ticket")


def _download_content(data_id: int, ticket: str) -> bytes:
    """Descarga el contenido binario de un documento."""
    url = f"{OTCS_BASE_URL}/api/v1/nodes/{data_id}/content"
    
    response = requests.get(
        url,
        headers={"OTCSTicket": ticket},
        timeout=OTCS_TIMEOUT,
        verify=False,
    )
    response.raise_for_status()
    
    return response.content


def load_from_opentext(data_id: int, metadata: dict = None) -> Document:
    """
    Descarga un PDF desde Content Server y lo parsea.
    
    Args:
        data_id: ID del documento en Content Server
        metadata: Metadata adicional (ej: de SQL Server)
    
    Returns:
        Document con el texto extraído
    """
    # 1. Autenticar
    ticket = _get_auth_ticket()
    
    # 2. Descargar
    content = _download_content(data_id, ticket)
    
    # 3. Parsear PDF
    pdf_file = io.BytesIO(content)
    reader = PdfReader(pdf_file)
    
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    
    # 4. Armar metadata
    doc_metadata = {
        "source": f"opentext://{data_id}",
        "data_id": data_id,
        "file_type": "pdf",
        "num_pages": len(reader.pages),
    }
    
    # Agregar metadata extra si viene
    if metadata:
        doc_metadata.update(metadata)
    
    return Document(content=text, metadata=doc_metadata)


def test_connection() -> bool:
    """Verifica que la conexión funcione."""
    try:
        ticket = _get_auth_ticket()
        return ticket is not None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return False


if __name__ == "__main__":
    # Test rápido
    import sys
    
    if len(sys.argv) > 1:
        data_id = int(sys.argv[1])
        doc = load_from_opentext(data_id)
        print(f"Descargado: {len(doc.content)} caracteres, {doc.metadata['num_pages']} páginas")
    else:
        print("Probando conexión...")
        if test_connection():
            print("✅ Conexión OK")
        else:
            print("❌ Conexión fallida")
