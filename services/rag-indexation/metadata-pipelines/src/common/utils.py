import os
import hashlib
import json
import uuid
from datetime import datetime

def generate_run_id():
    """Genera el run_id siguiendo el formato de la documentación."""
    return f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"

def calculate_checksum(data):
    """Calcula SHA-256 para cumplir con el requisito de integridad de Bronze."""
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

def save_json_artifact(data, path):
    """Guarda artefactos asegurando que las carpetas existan."""
    # Extraer el directorio de la ruta (ej: data/bronze)
    directory = os.path.dirname(path)
    
    # Crear la carpeta si no existe (incluye subcarpetas)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, default=str)